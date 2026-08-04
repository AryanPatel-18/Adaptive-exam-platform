from processing.models import Topic
from quiz.exceptions import QuizAttemptNotFoundException
from quiz.models import QuizAttempt, QuizAttemptAnswer
from .models import StudySchedule
from .exceptions import ScheduleNotFoundException
import logging

logger = logging.getLogger(__name__)




class ScheduleSelector:

    @staticmethod
    def get_schedule(schedule_id):
        """
        Retrieve a study schedule by its ID.
        """
        logger.debug("Fetching schedule with ID: %s", schedule_id)
        try:
            return (
                StudySchedule.objects.select_related(
                    "user",
                    "workspace",
                    "quiz_attempt",
                )
                .get(
                    id=schedule_id,
                )
            )

        except StudySchedule.DoesNotExist:
            raise ScheduleNotFoundException()

    @staticmethod
    def get_schedule_for_user(
        *,
        schedule_id,
        user,
    ):
        """
        Retrieve a study schedule belonging to the given user.
        """
        try:
            return (
                StudySchedule.objects.select_related(
                    "user",
                    "workspace",
                    "quiz_attempt",
                )
                .get(
                    id=schedule_id,
                    user=user,
                )
            )

        except StudySchedule.DoesNotExist:
            raise ScheduleNotFoundException()

    @staticmethod
    def get_latest_schedule(
        *,
        workspace,
    ):
        """
        Retrieve the latest active study schedule for a workspace.
        """
        return (
            StudySchedule.objects.select_related(
                "user",
                "workspace",
                "quiz_attempt",
            )
            .filter(
                workspace=workspace,
                is_active=True,
            )
            .order_by(
                "-created_at",
            )
            .first()
        )


class AttemptAnalysisSelector:

    @staticmethod
    def get_attempt(
        *,
        attempt_id,
        user,
    ):
        """
        Retrieve a completed quiz attempt with all required
        related objects.
        """
        logger.debug("Fetching completed quiz attempt: %s for user: %s", attempt_id, user.id)
        try:
            return (
                QuizAttempt.objects.select_related(
                    "quiz",
                    "quiz__workspace",
                    "user",
                )
                .get(
                    id=attempt_id,
                    user=user,
                    status=QuizAttempt.Status.COMPLETED,
                )
            )

        except QuizAttempt.DoesNotExist:
            raise QuizAttemptNotFoundException()

    @staticmethod
    def get_attempt_answers(
        *,
        attempt,
    ):
        """
        Retrieve all answers for an attempt with related
        questions, topics and selected options.
        """
        return (
            QuizAttemptAnswer.objects.select_related(
                "question",
                "selected_option",
            )
            .prefetch_related(
                "question__question_topics__topic",
            )
            .filter(
                attempt=attempt,
                answered_at__isnull=False,
            )
            .order_by(
                "question__question_number",
            )
        )

    @staticmethod
    def get_attempt_topics(
        *,
        workspace,
    ):
        """
        Retrieve all topics that belong to the workspace.
        """
        return (
            Topic.objects.filter(
                workspace=workspace,
            )
            .order_by(
                "name",
            )
        )

    @staticmethod
    def get_topic_answers(
        *,
        attempt,
        topic,
    ):
        """
        Retrieve all answered questions for a topic.
        """
        return (
            QuizAttemptAnswer.objects.select_related(
                "question",
                "selected_option",
            )
            .filter(
                attempt=attempt,
                question__question_topics__topic=topic,
                answered_at__isnull=False,
            )
            .order_by(
                "question__question_number",
            )
        )