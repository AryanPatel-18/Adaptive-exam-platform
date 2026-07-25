from uuid import UUID

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

class ProcessWorkspaceView(APIView):
    """
    Process a question bank file for a workspace.
    """

    def post(
        self,
        request: Request,
        workspace_id: UUID,
    ) -> Response:
        """
        Process a single question bank file.

        Args:
            request: Incoming HTTP request.
            workspace_id: Workspace identifier.
        """

        workspace = self._get_workspace(
            workspace_id=workspace_id,
            user=request.user,
        )

        source_file = self._get_source_file(
            workspace=workspace,
        )

        ProcessingService.process(
            workspace=workspace,
            source_file=source_file,
        )

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
    def _get_source_file(
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
                If the file does not exist or does not belong to the workspace.
        """
        source_file = File.objects.filter(
            workspace=workspace,
            role=FileRole.QUESTION_BANK,
        ).order_by("-created_at").first()

        if not source_file:
            raise FileNotFoundException("No question bank file found for this workspace.")
            
        return source_file