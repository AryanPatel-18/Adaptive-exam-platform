from django.conf import settings
from django.db import models

from common.models import BaseModel
from processing.models import Question, QuestionOption
from workspace.models import Workspace


class Quiz(BaseModel):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="quizzes",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_quizzes",
    )

    title = models.CharField(max_length=255)

    total_questions = models.PositiveIntegerField()

    class Meta:
        db_table = "quizzes"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workspace"]),
            models.Index(fields=["created_by"]),
        ]

    def __str__(self):
        return self.title


class QuizQuestion(BaseModel):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="quiz_questions",
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="quizzes",
    )

    order = models.PositiveIntegerField()

    class Meta:
        db_table = "quiz_questions"
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["quiz", "question"],
                name="unique_question_per_quiz",
            ),
            models.UniqueConstraint(
                fields=["quiz", "order"],
                name="unique_question_order_per_quiz",
            ),
        ]
        indexes = [
            models.Index(fields=["quiz"]),
            models.Index(fields=["question"]),
        ]

    def __str__(self):
        return f"{self.quiz.title} - Question {self.order}"


class QuizAttempt(BaseModel):
    class Status(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        ABANDONED = "ABANDONED", "Abandoned"

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="attempts",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )

    attempt_number = models.PositiveIntegerField(editable=False)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )

    started_at = models.DateTimeField(auto_now_add=True)

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    score = models.PositiveIntegerField(default=0)

    total_marks = models.PositiveIntegerField(default=0)

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    correct_answers = models.PositiveIntegerField(default=0)

    wrong_answers = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "quiz_attempts"
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["quiz", "user", "attempt_number"],
                name="unique_attempt_number_per_quiz",
            ),
        ]
        indexes = [
            models.Index(fields=["quiz"]),
            models.Index(fields=["user"]),
            models.Index(fields=["status"]),
            models.Index(fields=["completed_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} (Attempt {self.attempt_number})"


class QuizAttemptAnswer(BaseModel):
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="attempt_answers",
    )

    selected_option = models.ForeignKey(
        QuestionOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attempt_answers",
    )

    loaded_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    answered_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_correct = models.BooleanField(default=False)

    class Meta:
        db_table = "quiz_attempt_answers"
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "question"],
                name="unique_answer_per_attempt",
            ),
        ]
        indexes = [
            models.Index(fields=["attempt"]),
            models.Index(fields=["question"]),
        ]

    def __str__(self):
        return f"{self.attempt} - {self.question}"