from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.responses import success_response
from .models import Workspace
from .serializer import WorkspaceSerializer, UpdateWorkspaceSerializer, WorkspaceFileSerializer, WorkspaceDetailSerializer
from .service import WorkspaceService
from .selectors import WorkspaceSelector
from .exceptions import WorkspaceNotFoundException, WorkspacePermissionException
from quiz.serializers import QuizSerializer


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


class ListUserWorkspacesDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        workspaces = WorkspaceSelector.get_user_workspaces_details(request.user)
        response_data = WorkspaceDetailSerializer(workspaces, many=True).data

        return success_response(
            message="User workspaces retrieved successfully.",
            data=response_data,
            status_code=status.HTTP_200_OK,
        )


class ListWorkspaceFilesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id):
        workspace = Workspace.objects.filter(id=workspace_id).first()
        
        if not workspace:
            raise WorkspaceNotFoundException()
            
        if workspace.owner != request.user:
            raise WorkspacePermissionException()

        files_data = WorkspaceSelector.get_workspace_files(workspace_id=workspace_id)
        
        qb_data = WorkspaceFileSerializer(files_data["question_bank"]).data if files_data["question_bank"] else None
        notes_data = WorkspaceFileSerializer(files_data["notes"], many=True).data
        
        return success_response(
            message="Workspace files retrieved successfully.",
            data={
                "question_bank": qb_data,
                "notes": notes_data
            },
            status_code=status.HTTP_200_OK,
        )


class ListWorkspaceQuizzesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id):
        workspace = Workspace.objects.filter(id=workspace_id).first()
        
        if not workspace:
            raise WorkspaceNotFoundException()
            
        if workspace.owner != request.user:
            raise WorkspacePermissionException()

        quizzes = WorkspaceSelector.get_workspace_quizzes(workspace_id=workspace_id)
        quizzes_data = QuizSerializer(quizzes, many=True).data
        
        return success_response(
            message="Workspace quizzes retrieved successfully.",
            data=quizzes_data,
            status_code=status.HTTP_200_OK,
        )
