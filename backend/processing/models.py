from django.db import models
from django.db.models import Q

from common.choices import ProcessingStage, ProcessingStatus
from common.models import BaseModel
from workspace.models import Workspace
from files.models import File

class ProcessingJob(BaseModel):
    """
    Represents a single processing run for a workspace.
    """

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="processing_jobs",
    )

    status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
    )

    stage = models.CharField(
        max_length=30,
        choices=ProcessingStage.choices,
        default=ProcessingStage.INITIALIZED,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    failure_reason = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "processing_jobs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.workspace.title} ({self.status})"

class Topic(BaseModel):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="topics",
    )

    name = models.CharField(
        max_length=255,
    )

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=("workspace", "name"),
                name="unique_topic_per_workspace",
            )
        ]

    def __str__(self):
        return self.name

class TopicFile(BaseModel):
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="files",
    )

    file = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        related_name="topics",
    )

    class Meta:
        ordering = ("created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("topic", "file"),
                name="unique_topic_file_link",
            )
        ]

    def __str__(self):
        return f"{self.topic.name} - {self.file.original_filename}"

class Question(BaseModel):
    source_file = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    question_number = models.PositiveIntegerField()

    question_text = models.TextField()

    class Meta:
        ordering = ("question_number",)
        constraints = [
            models.UniqueConstraint(
                fields=("source_file", "question_number"),
                name="unique_question_per_file",
            )
        ]

    def __str__(self):
        return f"Q{self.question_number}"

class QuestionOption(BaseModel):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options",
    )

    text = models.TextField()

    is_correct = models.BooleanField(
        default=False,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("question", "text"),
                name="unique_option_per_question",
            ),
            models.UniqueConstraint(
                fields=("question",),
                condition=Q(is_correct=True),
                name="single_correct_option_per_question",
            ),
        ]

    def __str__(self):
        return self.text

class QuestionTopic(BaseModel):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="question_topics",
    )

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="question_topics",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("question", "topic"),
                name="unique_question_topic",
            )
        ]

    def __str__(self):
        return f"{self.question.question_number} - {self.topic.name}"