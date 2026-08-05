from django.urls import path

from .views import (
    CreateWorkspaceView,
    UpdateWorkspaceView,
    DeleteWorkspaceView,
    ListUserWorkspacesView,
    ListWorkspaceFilesView,
    ListWorkspaceQuizzesView,
    ListUserWorkspacesDetailsView,
)

urlpatterns = [
    path(
        "list/",
        ListUserWorkspacesDetailsView.as_view(),
        name="list-user-workspaces",
    ),
    path(
        "create/",
        CreateWorkspaceView.as_view(),
        name="create-workspace",
    ),
    path(
        "<uuid:workspace_id>/",
        UpdateWorkspaceView.as_view(),
        name="update-workspace",
    ),
    path(
        "<uuid:workspace_id>/delete/",
        DeleteWorkspaceView.as_view(),
        name="delete-workspace",
    ),
    path(
        "list/ids/",
        ListUserWorkspacesView.as_view(),
        name="list-user-workspaces-ids",
    ),
    path(
        "<uuid:workspace_id>/files/",
        ListWorkspaceFilesView.as_view(),
        name="list-workspace-files",
    ),
    path(
        "<uuid:workspace_id>/quizzes/",
        ListWorkspaceQuizzesView.as_view(),
        name="list-workspace-quizzes",
    ),
]