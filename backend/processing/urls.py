from django.urls import path
from .views import ProcessWorkspaceView

urlpatterns = [
    path(
        "<uuid:workspace_id>/process/",
        ProcessWorkspaceView.as_view(),
        name="process-workspace",
    ),
]