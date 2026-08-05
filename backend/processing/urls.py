from django.urls import path
from .views import ProcessWorkspaceView, CheckWorkspaceProcessingStatusView, GetWorkspaceProcessingProgressView

urlpatterns = [
    path(
        "<uuid:workspace_id>/process/",
        ProcessWorkspaceView.as_view(),
        name="process-workspace",
    ),
    path(
        "<uuid:workspace_id>/status/",
        CheckWorkspaceProcessingStatusView.as_view(),
        name="workspace-processing-status",
    ),
    path(
        "<uuid:workspace_id>/progress/",
        GetWorkspaceProcessingProgressView.as_view(),
        name="workspace-processing-progress",
    ),
]