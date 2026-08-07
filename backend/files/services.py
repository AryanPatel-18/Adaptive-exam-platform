from common.choices import WorkspaceStatus
import hashlib
import logging
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError, IntegrityError, transaction
from django.utils import timezone

from common.choices import UploadFileStatus, UploadSessionStatus, FileStatus
from files.exceptions import (
    DuplicateFileHashException,
    FileException,
    FileProcessingException,
    UploadedObjectContentTypeMismatchException,
    UploadedObjectIntegrityException,
    UploadedObjectNotFoundException,
    UploadedObjectSizeMismatchException,
    UploadSessionCompletedException,
    UploadSessionCompletionException,
    UploadSessionCreationException,
    UploadSessionExpiredException,
    UploadSessionFailedException,
    UploadSessionNotFoundException,
    UploadSessionStateException,
    UploadSessionVerificationException,
    VerifiedUploadSessionFileNotFoundException,
    WorkspaceArchivedException,
    WorkspaceNotFoundException,
    WorkspacePermissionException,
    WorkspaceProcessingInProgressException,
)
from files.models import File, UploadSession, UploadSessionFile
from storage.provider import MinIOProvider
from storage.utils import generate_storage_key

logger = logging.getLogger(__name__)


class FilesService:
    """
    Service responsible for orchestrating the entire upload workflow.

    This service coordinates:
        - Upload session creation.
        - Temporary upload file records.
        - Storage key generation.
        - Pre-signed URL generation.
        - Object verification against MinIO.
        - SHA-256 hash calculation.
        - Duplicate file detection.
        - Permanent File record creation.
        - Upload session completion.
    """

    provider = MinIOProvider()

    @staticmethod
    @transaction.atomic
    def create_upload_session(
        *,
        workspace,
        user,
        files: list[dict],
    ) -> dict:
        """
        Create an upload session and generate upload instructions.

        Args:
            workspace:
                Workspace receiving the uploaded files.

            user:
                User initiating the upload.

            files:
                List of validated file metadata.

        Returns:
            Dictionary containing upload session information and
            pre-signed upload URLs.
        """
        FilesService._validate_upload_workspace(
            workspace=workspace,
            user=user,
        )

        try:
            expected_total_size = sum(
                file["size"] for file in files
            )

            upload_session = UploadSession.objects.create(
                workspace=workspace,
                user=user,
                status=UploadSessionStatus.PENDING,
                expected_file_count=len(files),
                expected_total_size=expected_total_size,
                expires_at=timezone.now()
                + timedelta(
                    seconds=settings.UPLOAD_SESSION_EXPIRY_SECONDS
                ),
            )

            prepared_files = []

            for file in files:
                storage_key = generate_storage_key(
                    workspace_id=workspace.id,
                    upload_session_id=upload_session.id,
                    file_role=file["role"],
                    filename=file["filename"],
                )
                upload_url = FilesService.provider.generate_upload_url(
                    storage_key=storage_key,
                    content_type=file["content_type"],
                    expires_in=settings.UPLOAD_SESSION_EXPIRY_SECONDS
                )
                prepared_files.append((
                    UploadSessionFile(
                        upload_session=upload_session,
                        original_filename=file["filename"],
                        storage_key=storage_key,
                        role=file["role"],
                        status=UploadFileStatus.PENDING,
                        expected_file_size=file["size"],
                        expected_content_type=file["content_type"],
                    ),
                    upload_url,
                ))

            UploadSessionFile.objects.bulk_create(
                [session_file for session_file, _ in prepared_files]
            )

            logger.info(
                "Created upload session %s for workspace %s expecting %d files",
                upload_session.id, workspace.id, len(files)
            )

            return {
                "upload_session_id": upload_session.id,
                "expires_at": upload_session.expires_at,
                "files": [
                    {
                        "upload_session_file_id": session_file.id,
                        "original_filename": session_file.original_filename,
                        "role": session_file.role,
                        "storage_key": session_file.storage_key,
                        "content_type": session_file.expected_content_type,
                        "expected_file_size": session_file.expected_file_size,
                        "upload_url": upload_url,
                    }
                    for session_file, upload_url in prepared_files
                ],
            }

        except IntegrityError as exc:
            logger.warning("Upload session creation failed due to IntegrityError for workspace %s", workspace.id)
            raise UploadSessionCreationException(
                detail="Failed to create upload session."
            ) from exc

        except DatabaseError as exc:
            logger.error("Database error occurred while creating upload session for workspace %s: %s", workspace.id, exc, exc_info=True)
            raise UploadSessionCreationException(
                detail="Database error occurred while creating the upload session."
            ) from exc

        except Exception as exc:
            logger.error("Unexpected error occurred while creating upload session for workspace %s: %s", workspace.id, exc, exc_info=True)
            raise FileException(
                detail="Unexpected error occurred while creating the upload session."
            ) from exc

    @staticmethod
    def _validate_upload_workspace(
        *,
        workspace,
        user,
    ) -> None:
        """
        Validate that the workspace can accept uploaded files.

        Raises:
            WorkspaceNotFoundException:
                If the workspace does not exist.

            WorkspacePermissionException:
                If the user does not own the workspace.

            WorkspaceArchivedException:
                If the workspace has been archived.

            WorkspaceProcessingInProgressException:
                If the workspace is currently being processed.
        """

        if workspace is None:
            raise WorkspaceNotFoundException()

        if workspace.owner_id != user.id:
            raise WorkspacePermissionException()

        if workspace.status == WorkspaceStatus.ARCHIVED:
            raise WorkspaceArchivedException()

        if workspace.status == WorkspaceStatus.PROCESSING:
            raise WorkspaceProcessingInProgressException()


    @staticmethod
    @transaction.atomic
    def finalize_upload(upload_session_id, user):
        """
        Finalize an upload session.

        Workflow
        --------
        1. Retrieve and lock the upload session.
        2. Validate that the session is eligible for finalization.
        3. Mark the session as VERIFYING.
        4. Verify every uploaded object against MinIO.
        5. Register all verified objects as permanent File records.
        6. Mark the session as COMPLETED.
        7. Return a summary.

        Any failure during steps 4–5 causes the session to be rolled back
        to FAILED and all uploaded objects to be deleted from storage.
        """

        upload_session = FilesService._get_upload_session(
            upload_session_id=upload_session_id,
            user=user,
        )

        FilesService._verify_upload_session(
            upload_session=upload_session,
        )

        try:
            upload_session.status = UploadSessionStatus.VERIFYING
            upload_session.save(update_fields=["status", "updated_at"])
        except DatabaseError as exc:
            raise UploadSessionStateException(
                detail="Failed to update upload session status to VERIFYING."
            ) from exc

        try:
            FilesService._verify_uploaded_objects(
                upload_session=upload_session,
            )
            FilesService.register_verified_files(
                upload_session=upload_session,
            )

        except (
            UploadSessionVerificationException,
            UploadedObjectNotFoundException,
            UploadedObjectSizeMismatchException,
            UploadedObjectContentTypeMismatchException,
            UploadedObjectIntegrityException,
            VerifiedUploadSessionFileNotFoundException,
            DuplicateFileHashException,
            FileProcessingException,
        ) as processing_exception:

            logger.error("Verification failed for upload session %s: %s", upload_session.id, processing_exception)

            try:
                FilesService._fail_upload_session(
                    upload_session=upload_session,
                    failure_reason=str(processing_exception),
                )
            except (UploadSessionStateException, DatabaseError) as rollback_exc:
                logger.error("Failed to roll back upload session %s: %s", upload_session.id, rollback_exc, exc_info=True)

            raise processing_exception

        FilesService._complete_upload_session(
            upload_session=upload_session,
        )

        upload_session.refresh_from_db()

        logger.info(
            "Successfully completed upload session %s with %d verified files.",
            upload_session.id, upload_session.uploaded_file_count
        )

        return {
            "upload_session_id": upload_session.id,
            "status": upload_session.status,
            "verified_file_count": upload_session.uploaded_file_count,
            "completed_at": upload_session.completed_at,
        }

    @staticmethod
    @transaction.atomic
    def register_verified_files(upload_session) -> list:
        """
        Register all verified upload session files as permanent File records.

        Workflow
        --------
        Pass 1 — Preparation
            Calculates the SHA-256 hash for each uploaded file and prepares a
            unique registration batch by ignoring duplicate files within the
            current upload session.

        Pass 2 — Persistence
            For each prepared file:

                If a matching file already exists in the workspace:
                    1. Reactivate the existing File record.

                Otherwise:
                    1. Create a new permanent File record.

                Finally:
                    2. Mark the UploadSessionFile as REGISTERED.

        Returns
        -------
        list[File]
            List of active File records associated with the workspace.

        Raises
        ------
        VerifiedUploadSessionFileNotFoundException
        FileProcessingException
        """

        upload_session_files = FilesService._get_verified_upload_session_files(
            upload_session=upload_session,
        )

        # ------------------------------------------------------------------
        # Pass 1: Prepare unique files for registration
        # ------------------------------------------------------------------

        prepared_files = FilesService._prepare_file_registration(
            upload_session_files=upload_session_files,
        )

        # ------------------------------------------------------------------
        # Pass 2: Reactivate existing files or create new permanent files
        # ------------------------------------------------------------------

        registered_files: list[File] = []

        for upload_session_file, file_hash in prepared_files:

            existing_file = FilesService._get_existing_workspace_file(
                workspace=upload_session.workspace,
                file_hash=file_hash,
            )

            if existing_file:
                FilesService._activate_existing_file(
                    file=existing_file,
                )
                # Delete the redundant object from storage. The permanent
                # File record points to the original upload's storage key,
                # so the new copy is safe to remove.
                try:
                    FilesService.provider.delete_object(
                        storage_key=upload_session_file.storage_key,
                    )
                except Exception:
                    logger.exception(
                        "Failed to delete redundant object %s from storage "
                        "after reactivating existing file %s.",
                        upload_session_file.storage_key,
                        existing_file.id,
                    )
                permanent_file = existing_file

            else:
                permanent_file = FilesService._create_permanent_file(
                    upload_session_file=upload_session_file,
                    file_hash=file_hash,
                )

            FilesService._mark_upload_session_file_registered(
                upload_session_file=upload_session_file,
            )

            registered_files.append(permanent_file)

        logger.info("Successfully registered %d permanent files for upload session %s", len(registered_files), upload_session.id)
        return registered_files

    # ------------------------------------------------------------------
    # Private helpers — Session retrieval & validation
    # ------------------------------------------------------------------

    @staticmethod
    def _get_upload_session(upload_session_id, user):
        """
        Retrieve and lock an upload session belonging to the authenticated user.

        The upload session is locked using SELECT FOR UPDATE to prevent
        concurrent finalization requests.

        Raises
        ------
        UploadSessionNotFoundException
            If the upload session does not exist or does not belong to the user.
        """

        try:
            return (
                UploadSession.objects
                .select_for_update()
                .select_related("workspace")
                .get(
                    id=upload_session_id,
                    user=user,
                )
            )

        except ObjectDoesNotExist as exc:
            raise UploadSessionNotFoundException() from exc

    @staticmethod
    def _verify_upload_session(upload_session):
        """
        Validate that the upload session is eligible for finalization.

        Checks
        ------
        - Upload session has not expired.
        - Upload session is not already completed.
        - Upload session is not already failed.
        - Upload session is in the PENDING state.

        Raises
        ------
        UploadSessionExpiredException
        UploadSessionCompletedException
        UploadSessionFailedException
        UploadSessionStateException
        """

        if upload_session.expires_at <= timezone.now():
            raise UploadSessionExpiredException()

        if upload_session.status == UploadSessionStatus.COMPLETED:
            raise UploadSessionCompletedException()

        if upload_session.status == UploadSessionStatus.FAILED:
            raise UploadSessionFailedException()

        if upload_session.status != UploadSessionStatus.PENDING:
            raise UploadSessionStateException()

    # ------------------------------------------------------------------
    # Private helpers — Object verification
    # ------------------------------------------------------------------

    @staticmethod
    def _verify_uploaded_objects(upload_session):
        """
        Verify every uploaded object belonging to the upload session.

        This method performs verification in two phases:

        Phase 1
        -------
        Validate every uploaded object against object storage.

        Phase 2
        -------
        Persist verification metadata for every successfully verified object.

        Raises
        ------
        UploadSessionVerificationException
        UploadedObjectNotFoundException
        UploadedObjectSizeMismatchException
        UploadedObjectContentTypeMismatchException
        UploadedObjectIntegrityException
        """

        upload_session_files = FilesService._get_upload_session_files(
            upload_session=upload_session,
        )

        verified_objects = []

        for upload_session_file in upload_session_files:

            metadata = FilesService.provider.get_object_metadata(
                storage_key=upload_session_file.storage_key,
            )

            FilesService._verify_uploaded_object(
                upload_session_file=upload_session_file,
                metadata=metadata,
            )

            verified_objects.append(
                (
                    upload_session_file,
                    metadata,
                )
            )

        for upload_session_file, metadata in verified_objects:

            FilesService._update_upload_session_file(
                upload_session_file=upload_session_file,
                metadata=metadata,
            )

    @staticmethod
    def _verify_uploaded_object(upload_session_file, metadata):
        """
        Verify that an uploaded object's metadata matches the expected metadata.

        Parameters
        ----------
        upload_session_file : UploadSessionFile
            Upload session file containing the expected metadata.

        metadata : dict
            Normalized metadata returned by the storage provider.

        Raises
        ------
        UploadedObjectIntegrityException
            If the uploaded object is empty or contains invalid metadata.

        UploadedObjectSizeMismatchException
            If the uploaded object's size does not match the expected size.

        UploadedObjectContentTypeMismatchException
            If the uploaded object's content type does not match the expected
            content type.
        """

        content_length = metadata["content_length"]
        content_type = metadata["content_type"]

        if not isinstance(content_length, int) or content_length <= 0:
            logger.warning(
                "Verification failed: Invalid content_length %s for file %s",
                content_length, upload_session_file.id
            )
            raise UploadedObjectIntegrityException()

        expected_content_type = (
            upload_session_file.expected_content_type
            .split(";")[0]
            .strip()
            .lower()
        )

        uploaded_content_type = (
            content_type
            .split(";")[0]
            .strip()
            .lower()
        )

        if content_length != upload_session_file.expected_file_size:
            logger.warning(
                "Verification failed: Size mismatch for file %s (Expected: %s, Actual: %s)",
                upload_session_file.id, upload_session_file.expected_file_size, content_length
            )
            raise UploadedObjectSizeMismatchException()

        if uploaded_content_type != expected_content_type:
            logger.warning(
                "Verification failed: Content type mismatch for file %s (Expected: %s, Actual: %s)",
                upload_session_file.id, expected_content_type, uploaded_content_type
            )
            raise UploadedObjectContentTypeMismatchException()

    @staticmethod
    def _get_upload_session_files(upload_session):
        """
        Retrieve all UploadSessionFile records belonging to an upload session.

        Raises
        ------
        UploadSessionVerificationException
            If the upload session does not contain any associated files.
        """

        upload_session_files = (
            UploadSessionFile.objects
            .filter(upload_session=upload_session)
            .order_by("created_at")
        )

        if not upload_session_files.exists():
            raise UploadSessionVerificationException(
                detail="The upload session does not contain any files."
            )

        return upload_session_files

    @staticmethod
    def _update_upload_session_file(upload_session_file, metadata):
        """
        Persist verified metadata for an uploaded object.

        Parameters
        ----------
        upload_session_file : UploadSessionFile
            The upload session file to update.

        metadata : dict
            Normalized object metadata returned by the storage provider.

        Raises
        ------
        UploadSessionVerificationException
            If the metadata cannot be persisted to the database.
        """

        upload_session_file.uploaded_file_size = metadata["content_length"]
        upload_session_file.uploaded_content_type = metadata["content_type"]
        upload_session_file.etag = metadata["etag"]
        upload_session_file.object_last_modified = metadata["last_modified"]
        upload_session_file.verified_at = timezone.now()
        upload_session_file.status = UploadFileStatus.VERIFIED

        try:
            upload_session_file.save(
                update_fields=[
                    "uploaded_file_size",
                    "uploaded_content_type",
                    "etag",
                    "object_last_modified",
                    "verified_at",
                    "status",
                    "updated_at",
                ]
            )
        except DatabaseError as exc:
            logger.error(
                "Failed to persist verified metadata for file %s: %s",
                upload_session_file.id, exc, exc_info=True
            )
            raise UploadSessionVerificationException(
                detail="Failed to persist verified metadata to the database."
            ) from exc

    # ------------------------------------------------------------------
    # Private helpers — Session failure / rollback
    # ------------------------------------------------------------------

    @staticmethod
    def _fail_upload_session(upload_session, failure_reason):
        """
        Roll back an upload session.

        Workflow
        --------
        1. Delete uploaded objects from storage.
        2. Mark UploadSessionFile records as failed.
        3. Mark UploadSession as failed.
        """
        
        logger.warning(
            "Rolling back upload session %s due to failure: %s",
            upload_session.id, failure_reason
        )

        upload_session_files = UploadSessionFile.objects.filter(
            upload_session=upload_session,
        )

        for session_file in upload_session_files:
            try:
                FilesService.provider.delete_object(
                    storage_key=session_file.storage_key,
                )
            except Exception:
                logger.exception(
                    f"Failed to delete object {session_file.storage_key} "
                    f"from storage during rollback of upload session {upload_session.id}."
                )

        FilesService._mark_upload_session_files_failed(
            upload_session=upload_session,
            failure_reason=failure_reason,
        )

        FilesService._mark_upload_session_failed(
            upload_session=upload_session,
        )

    @staticmethod
    def _mark_upload_session_files_failed(upload_session, failure_reason):
        """
        Mark every non-registered UploadSessionFile in the upload session as
        failed.

        Files that have already been registered are left unchanged.
        """

        (
            UploadSessionFile.objects
            .filter(upload_session=upload_session)
            .exclude(status=UploadFileStatus.REGISTERED)
            .update(
                status=UploadFileStatus.FAILED,
                failure_reason=failure_reason,
            )
        )

    @staticmethod
    def _mark_upload_session_failed(upload_session):
        """
        Mark the upload session as failed.

        Updates
        -------
        - status
        - updated_at
        """

        try:
            upload_session.status = UploadSessionStatus.FAILED

            upload_session.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        except DatabaseError as exc:
            raise UploadSessionStateException(
                detail="Failed to mark the upload session as failed."
            ) from exc

    @staticmethod
    def _complete_upload_session(upload_session):
        """
        Mark an upload session as successfully completed.

        Updates
        -------
        - status
        - completed_at
        - uploaded_file_count (counted from REGISTERED UploadSessionFile records)
        """

        try:
            upload_session.status = UploadSessionStatus.COMPLETED
            upload_session.completed_at = timezone.now()
            upload_session.uploaded_file_count = (
                UploadSessionFile.objects.filter(
                    upload_session=upload_session,
                    status=UploadFileStatus.REGISTERED,
                ).count()
            )

            upload_session.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "uploaded_file_count",
                    "updated_at",
                ]
            )

        except DatabaseError as exc:
            raise UploadSessionCompletionException(
                "Failed to complete the upload session."
            ) from exc

    # ------------------------------------------------------------------
    # Private helpers — Permanent file registration
    # ------------------------------------------------------------------

    @staticmethod
    def _get_verified_upload_session_files(upload_session):
        """
        Retrieve all verified UploadSessionFile records belonging to an upload
        session.

        Raises
        ------
        VerifiedUploadSessionFileNotFoundException
            If the upload session contains no files in the VERIFIED state.
        """

        upload_session_files = (
            UploadSessionFile.objects
            .filter(
                upload_session=upload_session,
                status=UploadFileStatus.VERIFIED,
            )
            .order_by("created_at")
        )

        if not upload_session_files.exists():
            raise VerifiedUploadSessionFileNotFoundException()

        return upload_session_files

    @staticmethod
    def _prepare_file_registration(upload_session_files) -> list:
        """
        Prepare unique files for registration by calculating their SHA-256 hashes.

        Duplicate files within the current upload batch are ignored so that only
        one instance of each unique file proceeds to the registration phase.

        Returns
        -------
        list
            List of tuples containing:

            (
                UploadSessionFile,
                file_hash,
            )
        """

        prepared_files = []
        seen_hashes = set()

        for upload_session_file in upload_session_files:
            file_hash = FilesService._calculate_file_hash(
                upload_session_file=upload_session_file,
            )

            if file_hash in seen_hashes:
                # Delete the duplicate object from storage to prevent
                # an orphaned object leak.
                try:
                    FilesService.provider.delete_object(
                        storage_key=upload_session_file.storage_key,
                    )
                except Exception:
                    logger.exception(
                        "Failed to delete intra-batch duplicate object %s "
                        "from storage.",
                        upload_session_file.storage_key,
                    )
                # Mark the session file so it is not left in VERIFIED state.
                upload_session_file.status = UploadFileStatus.FAILED
                upload_session_file.failure_reason = (
                    "Duplicate file detected within the same upload batch."
                )
                upload_session_file.save(
                    update_fields=["status", "failure_reason", "updated_at"]
                )
                continue

            seen_hashes.add(file_hash)

            prepared_files.append(
                (
                    upload_session_file,
                    file_hash,
                )
            )

        return prepared_files

    @staticmethod
    def _calculate_file_hash(upload_session_file) -> str:
        """
        Calculate the SHA-256 hash of an uploaded object stored in MinIO.

        Streams the object in 1 MB chunks to avoid loading the entire file
        into memory. Uses the class-level provider instance.

        Parameters
        ----------
        upload_session_file : UploadSessionFile

        Returns
        -------
        str
            SHA-256 hexadecimal digest.

        Raises
        ------
        FileProcessingException
            If the file cannot be retrieved or hashed.
        """

        response = None
        try:
            response = FilesService.provider.get_object(
                storage_key=upload_session_file.storage_key,
            )

            hasher = hashlib.sha256()

            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                hasher.update(chunk)

            return hasher.hexdigest()

        except Exception as exc:
            logger.error(
                "Failed to calculate SHA-256 hash for storage key %s: %s",
                upload_session_file.storage_key, exc, exc_info=True
            )
            raise FileProcessingException(
                "Failed to calculate the SHA-256 hash of the uploaded file."
            ) from exc
        finally:
            if response is not None:
                response.close()

    @staticmethod
    def _get_existing_workspace_file(
        *,
        workspace,
        file_hash: str,
    ) -> File | None:
        """
        Retrieve an existing file with the given hash that already belongs to the
        specified workspace.

        Parameters
        ----------
        workspace
            Workspace that will own the file.

        file_hash : str
            SHA-256 hash of the uploaded file.

        Returns
        -------
        File | None
            The existing file if found, otherwise None.
        """

        return File.objects.filter(
            workspace=workspace,
            file_hash=file_hash,
        ).first()

    @staticmethod
    def _activate_existing_file(
        *,
        file: File,
    ) -> None:
        """
        Reactivate an existing workspace file.

        Parameters
        ----------
        file : File
            Existing permanent file belonging to the workspace.
        """

        if file.status != FileStatus.ACTIVE:
            file.status = FileStatus.ACTIVE
            file.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

    @staticmethod
    def _create_permanent_file(upload_session_file, file_hash: str):
        """
        Create a permanent File record from a verified UploadSessionFile.

        Parameters
        ----------
        upload_session_file : UploadSessionFile

        file_hash : str
            SHA-256 hexadecimal digest of the uploaded object.

        Returns
        -------
        File

        Raises
        ------
        FileProcessingException
            If the permanent File record cannot be created.
        """

        try:
            return File.objects.create(
                workspace=upload_session_file.upload_session.workspace,
                uploaded_by=upload_session_file.upload_session.user,
                upload_session=upload_session_file.upload_session,
                original_filename=upload_session_file.original_filename,
                storage_key=upload_session_file.storage_key,
                role=upload_session_file.role,
                mime_type=upload_session_file.uploaded_content_type,
                file_size=upload_session_file.uploaded_file_size,
                file_hash=file_hash,
            )

        except IntegrityError as exc:
            raise DuplicateFileHashException() from exc
        except DatabaseError as exc:
            logger.error(
                "Database error while creating permanent file for session file %s: %s",
                upload_session_file.id, exc, exc_info=True
            )
            raise FileProcessingException(
                "Failed to create the permanent file record."
            ) from exc

    @staticmethod
    def _mark_upload_session_file_registered(upload_session_file) -> None:
        """
        Mark an UploadSessionFile as successfully registered.

        Parameters
        ----------
        upload_session_file : UploadSessionFile

        Raises
        ------
        FileProcessingException
            If the status update cannot be persisted.
        """

        try:
            upload_session_file.status = UploadFileStatus.REGISTERED

            upload_session_file.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        except DatabaseError as exc:
            raise FileProcessingException(
                "Failed to mark the upload session file as registered."
            ) from exc