from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.responses import success_response
from .models import Workspace
from .serializer import WorkspaceSerializer, UpdateWorkspaceSerializer
from .service import WorkspaceService


class CreateWorkspaceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WorkspaceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        workspace = WorkspaceService.create_workspace(
            owner=request.user,
            title=serializer.validated_data["title"],
            description=serializer.validated_data.get("description", ""),
        )

        response_serializer = WorkspaceSerializer(workspace)

        return success_response(
            message="Workspace created successfully.",
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED,
        )



class UpdateWorkspaceView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, workspace_id):
        serializer = UpdateWorkspaceSerializer(
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        workspace = WorkspaceService.update_workspace(
            workspace_id=workspace_id,
            owner=request.user,
            title=serializer.validated_data.get("title"),
            description=serializer.validated_data.get("description"),
        )

        response_serializer = WorkspaceSerializer(workspace)

        return success_response(
            message="Workspace updated successfully.",
            data=response_serializer.data,
            status_code=status.HTTP_200_OK,
        )



class DeleteWorkspaceView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, workspace_id):
        WorkspaceService.delete_workspace(
            workspace_id=workspace_id,
            owner=request.user,
        )

        return success_response(
            message="Workspace deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK,
        )


class ListUserWorkspacesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        workspace_ids = Workspace.objects.filter(
            owner=request.user
        ).values_list("id", flat=True)

        return success_response(
            message="Workspace IDs retrieved successfully.",
            data=list(workspace_ids),
            status_code=status.HTTP_200_OK,
        )