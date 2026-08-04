import logging
from uuid import UUID

logger = logging.getLogger("processing")

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.choices import FileRole
from files.exceptions import FileNotFoundException
from files.models import File
from processing.services.processing_service import ProcessingService
from workspace.exceptions import WorkspaceNotFoundException
from workspace.models import Workspace
from common.choices import ProcessingStatus, ProcessingStage
from processing.models import ProcessingJob
from django.utils import timezone

class ProcessWorkspaceView(APIView):
    """
    Process files (question bank and notes) for a workspace.
    """

    def post(
        self,
        request: Request,
        workspace_id: UUID,
    ) -> Response:
        """
        Process the latest question bank and notes files for a workspace.

        Args:
            request: Incoming HTTP request.
            workspace_id: Workspace identifier.
        """

        logger.info("Processing requested for workspace_id=%s", workspace_id)

        workspace = self._get_workspace(
            workspace_id=workspace_id,
            user=request.user,
        )

        question_bank_file = self._get_question_bank_file(
            workspace=workspace,
        )

        notes_file = self._get_notes_file(
            workspace=workspace,
        )

        logger.info("Creating ProcessingJob for workspace_id=%s", workspace.id)
        job = ProcessingJob.objects.create(
            workspace=workspace,
            status=ProcessingStatus.RUNNING,
            stage=ProcessingStage.INITIALIZED,
        )

        try:
            logger.info("Question bank processing started for file_id=%s", question_bank_file.id)
            ProcessingService.process(
                workspace=workspace,
                source_file=question_bank_file,
                job=job,
            )

            logger.info("Notes processing started for file_id=%s", notes_file.id)
            ProcessingService.process_notes(
                workspace=workspace,
                source_file=notes_file,
                job=job,
            )

            job.status = ProcessingStatus.COMPLETED
            job.stage = ProcessingStage.FINISHED
            job.completed_at = timezone.now()
            job.save()
            
            logger.info("Processing completed successfully for workspace_id=%s", workspace.id)
        except Exception as exc:
            job.status = ProcessingStatus.FAILED
            job.failure_reason = str(exc)
            job.save()
            logger.error("Processing failed for workspace_id=%s: %s", workspace.id, exc)
            raise

        return Response(
            {
                "detail": "Processing completed successfully.",
            },
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _get_workspace(
        workspace_id: UUID,
        user,
    ) -> Workspace:
        """
        Retrieve the workspace to be processed.

        Args:
            workspace_id: Workspace identifier.
            user: Requesting user.

        Returns:
            Workspace instance.

        Raises:
            WorkspaceNotFoundException:
                If the workspace does not exist or user doesn't have access.
        """
        try:
            return Workspace.objects.get(
                id=workspace_id,
                owner=user,
            )
        except Workspace.DoesNotExist as exc:
            raise WorkspaceNotFoundException() from exc

    @staticmethod
    def _get_question_bank_file(
        workspace: Workspace,
    ) -> File:
        """
        Retrieve the latest question bank file to be processed for the workspace.

        Args:
            workspace: Workspace instance.

        Returns:
            File instance.

        Raises:
            FileNotFoundException:
                If the question bank file does not exist.
        """
        source_file = File.objects.filter(
            workspace=workspace,
            role=FileRole.QUESTION_BANK,
        ).order_by("-created_at").first()

        if not source_file:
            raise FileNotFoundException("No question bank file found for this workspace.")
            
        return source_file

    @staticmethod
    def _get_notes_file(
        workspace: Workspace,
    ) -> File:
        """
        Retrieve the latest notes file to be processed for the workspace.

        Args:
            workspace: Workspace instance.

        Returns:
            File instance.

        Raises:
            FileNotFoundException:
                If the notes file does not exist.
        """
        notes_file = File.objects.filter(
            workspace=workspace,
            role=FileRole.NOTES,
        ).order_by("-created_at").first()

        if not notes_file:
            raise FileNotFoundException("No notes file found for this workspace.")
            
        return notes_file