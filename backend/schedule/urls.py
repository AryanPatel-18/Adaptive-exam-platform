from django.urls import path

from schedule.views import (
    GenerateScheduleAPIView,
    LatestStudyScheduleAPIView,
    StudyScheduleAPIView,
    WorkspaceStudySchedulesAPIView,
)

app_name = "schedule"

urlpatterns = [
    path(
        "generate/",
        GenerateScheduleAPIView.as_view(),
        name="generate-schedule",
    ),
    path(
        "<uuid:schedule_id>/",
        StudyScheduleAPIView.as_view(),
        name="study-schedule",
    ),
    path(
        "latest/<uuid:workspace_id>/",
        LatestStudyScheduleAPIView.as_view(),
        name="latest-study-schedule",
    ),
    path(
        "workspace/<uuid:workspace_id>/",
        WorkspaceStudySchedulesAPIView.as_view(),
        name="workspace-study-schedules",
    ),
]