from django.urls import path

from schedule.views import (
    GenerateScheduleAPIView,
    LatestStudyScheduleAPIView,
    StudyScheduleAPIView,
    WorkspaceStudySchedulesAPIView,
    ToggleScheduleTopicAPIView,
    ScheduleJobStatusAPIView,
    WorkspaceScheduleJobStatusAPIView,
)

app_name = "schedule"

urlpatterns = [
    path(
        "generate/",
        GenerateScheduleAPIView.as_view(),
        name="generate-schedule",
    ),
    path(
        "job/<uuid:job_id>/",
        ScheduleJobStatusAPIView.as_view(),
        name="schedule-job-status",
    ),
    path(
        "workspace/<uuid:workspace_id>/job/",
        WorkspaceScheduleJobStatusAPIView.as_view(),
        name="workspace-schedule-job-status",
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
    path(
        "<uuid:schedule_id>/topic/<int:topic_index>/toggle/",
        ToggleScheduleTopicAPIView.as_view(),
        name="toggle-schedule-topic",
    ),
]