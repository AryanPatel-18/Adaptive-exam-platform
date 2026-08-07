from django.db import models
from common.models import BaseModel
from django.conf import settings
from workspace.models import Workspace
from quiz.models import QuizAttempt

class StudySchedule(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_schedules",
    )

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="study_schedules",
    )

    quiz_attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="study_schedules",
    )

    preparedness_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    generated_plan = models.JSONField()

    hours_per_day = models.DecimalField(
        max_digits=4,
        decimal_places=2,
    )

    start_date = models.DateField()

    end_date = models.DateField()

    is_active = models.BooleanField(
        default=True,
    )

    model_version = models.CharField(
        max_length=20,
        default="v1",
    )

    class Meta:
        db_table = "study_schedules"

        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["workspace"]),
            models.Index(fields=["quiz_attempt"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return (
            f"{self.workspace.title} - "
            f"{self.preparedness_score}%"
        )

class ScheduleGenerationJob(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="schedule_generation_jobs",
    )

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="schedule_generation_jobs",
    )

    status = models.CharField(
        max_length=20,
        default="PENDING",
    )

    schedule = models.ForeignKey(
        StudySchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generation_jobs",
    )

    failure_reason = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "schedule_generation_jobs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.workspace.title} - {self.status}"
