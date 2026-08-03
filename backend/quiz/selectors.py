from django.db.models import Prefetch

from processing.models import Question, QuestionOption
from quiz.exceptions import (
    InvalidQuestionException,
    QuizAttemptNotFoundException,
    QuizNotFoundException,
)
from quiz.models import Quiz, QuizAttempt, QuizAttemptAnswer, QuizQuestion
from workspace.exceptions import WorkspaceNotFoundException
from workspace.models import Workspace


class QuizSelector:

    @staticmethod
    def get_quiz(quiz_id):
        try:
            return Quiz.objects.select_related(
                "workspace",
                "created_by",
            ).get(id=quiz_id)

        except Quiz.DoesNotExist:
            raise QuizNotFoundException()

    @staticmethod
    def get_quiz_for_user(quiz_id, user):
        try:
            return Quiz.objects.select_related(
                "workspace",
                "created_by",
            ).get(
                id=quiz_id,
                created_by=user,
            )

        except Quiz.DoesNotExist:
            raise QuizNotFoundException()


class AttemptSelector:

    @staticmethod
    def get_attempt(attempt_id):
        try:
            return QuizAttempt.objects.select_related(
                "quiz",
                "user",
            ).get(id=attempt_id)

        except QuizAttempt.DoesNotExist:
            raise QuizAttemptNotFoundException()

    @staticmethod
    def get_attempt_for_user(attempt_id, user):
        try:
            return QuizAttempt.objects.select_related(
                "quiz",
                "user",
            ).get(
                id=attempt_id,
                user=user,
            )

        except QuizAttempt.DoesNotExist:
            raise QuizAttemptNotFoundException()

    @staticmethod
    def get_latest_attempt(quiz, user):
        return (
            QuizAttempt.objects.filter(
                quiz=quiz,
                user=user,
            )
            .order_by("-attempt_number")
            .first()
        )


class QuestionSelector:

    @staticmethod
    def get_question_by_order(
        *,
        quiz,
        order,
    ):
        try:
            return (
                QuizQuestion.objects.select_related(
                    "question",
                )
                .prefetch_related(
                    Prefetch(
                        "question__options",
                        queryset=QuestionOption.objects.order_by("id"),
                    )
                )
                .get(
                    quiz=quiz,
                    order=order,
                )
            )

        except QuizQuestion.DoesNotExist:
            raise InvalidQuestionException()

    @staticmethod
    def get_questions_for_workspace(workspace):
        return (
            Question.objects.filter(
                source_file__workspace=workspace,
            )
            .order_by("question_number")
        )

    @staticmethod
    def get_questions(quiz):
        return (
            QuizQuestion.objects.filter(
                quiz=quiz,
            )
            .select_related(
                "question",
            )
            .prefetch_related(
                Prefetch(
                    "question__options",
                    queryset=QuestionOption.objects.order_by("id"),
                )
            )
            .order_by("order")
        )



class WorkspaceSelector:

    @staticmethod
    def get_workspace(workspace_id):
        """
        Retrieve a workspace by its ID.
        """
        try:
            return Workspace.objects.get(id=workspace_id)

        except Workspace.DoesNotExist:
            raise WorkspaceNotFoundException()

    @staticmethod
    def get_workspace_for_user(workspace_id, user):
        """
        Retrieve a workspace owned by the given user.
        """
        try:
            return Workspace.objects.select_related(
                "owner",
            ).get(
                id=workspace_id,
                owner=user,
            )

        except Workspace.DoesNotExist:
            raise WorkspaceNotFoundException()


class AttemptAnswerSelector:

    @staticmethod
    def get_attempt_answer(
        *,
        attempt,
        question,
    ):
        try:
            return QuizAttemptAnswer.objects.get(
                attempt=attempt,
                question=question,
            )

        except QuizAttemptAnswer.DoesNotExist:
            return None

    @staticmethod
    def question_answered(
        *,
        attempt,
        question,
    ):
        return QuizAttemptAnswer.objects.filter(
            attempt=attempt,
            question=question,
        ).exists()