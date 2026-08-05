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

class CheckWorkspaceProcessingStatusView(APIView):
    def get(self, request: Request, workspace_id: UUID) -> Response:
        try:
            workspace = Workspace.objects.get(id=workspace_id, owner=request.user)
            is_processed = workspace.status == "READY"
            return Response(
                {
                    "is_processed": is_processed,
                    "status": workspace.status,
                },
                status=status.HTTP_200_OK,
            )
        except Workspace.DoesNotExist:
            return Response(
                {"detail": "Workspace not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

class GetWorkspaceProcessingProgressView(APIView):
    def get(self, request: Request, workspace_id: UUID) -> Response:
        try:
            workspace = Workspace.objects.get(id=workspace_id, owner=request.user)
            
            latest_job = ProcessingJob.objects.filter(workspace=workspace).order_by('-created_at').first()
            
            if not latest_job:
                return Response(
                    {"detail": "No processing jobs found for this workspace."},
                    status=status.HTTP_404_NOT_FOUND,
                )
                
            return Response(
                {
                    "status": latest_job.status,
                    "stage": latest_job.stage,
                    "created_at": latest_job.created_at,
                    "completed_at": latest_job.completed_at,
                    "failure_reason": latest_job.failure_reason,
                },
                status=status.HTTP_200_OK,
            )
        except Workspace.DoesNotExist:
            return Response(
                {"detail": "Workspace not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

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

        import threading
        
        def run_pipeline(ws_id, qb_id, notes_id, job_id):
            from django.utils import timezone
            
            ws = None
            # Re-fetch inside thread to ensure fresh connections
            try:
                ws = Workspace.objects.get(id=ws_id)
                qb = File.objects.get(id=qb_id)
                notes = File.objects.get(id=notes_id)
                job_instance = ProcessingJob.objects.get(id=job_id)
                
                logger.info("Question bank processing started for file_id=%s", qb.id)
                ProcessingService.process(
                    workspace=ws,
                    source_file=qb,
                    job=job_instance,
                )

                logger.info("Notes processing started for file_id=%s", notes.id)
                ProcessingService.process_notes(
                    workspace=ws,
                    source_file=notes,
                    job=job_instance,
                )

                job_instance.status = ProcessingStatus.COMPLETED
                job_instance.stage = ProcessingStage.FINISHED
                job_instance.completed_at = timezone.now()
                job_instance.save()
                
                # Mark workspace as ready
                ws.status = "READY"
                ws.save(update_fields=["status"])
                
                logger.info("Processing completed successfully for workspace_id=%s", ws.id)
            except Exception as exc:
                logger.error("Processing failed for workspace_id=%s: %s", ws_id, exc)
                
                # Use filter().update() or first() to avoid UnboundLocalError
                job_instance = ProcessingJob.objects.filter(id=job_id).first()
                if job_instance:
                    job_instance.status = ProcessingStatus.FAILED
                    job_instance.failure_reason = str(exc)
                    job_instance.save()
                
                if ws:
                    ws.status = "FAILED"
                    ws.save(update_fields=["status"])
                else:
                    Workspace.objects.filter(id=ws_id).update(status="FAILED")

        # Start processing in a background thread
        thread = threading.Thread(
            target=run_pipeline,
            args=(workspace.id, question_bank_file.id, notes_file.id, job.id)
        )
        thread.daemon = True
        thread.start()

        return Response(
            {
                "detail": "Processing started in background.",
                "job_id": job.id,
            },
            status=status.HTTP_202_ACCEPTED,
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