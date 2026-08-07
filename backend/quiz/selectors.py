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


class QuizStatsSelector:

    @staticmethod
    def get_workspace_quiz_stats(workspace_id, user):
        from django.db.models import Count, Avg, Sum, Case, When, IntegerField

        quizzes = Quiz.objects.filter(workspace_id=workspace_id, created_by=user)
        total_quizzes = quizzes.count()

        attempts = QuizAttempt.objects.filter(
            quiz__workspace_id=workspace_id,
            user=user,
            status=QuizAttempt.Status.COMPLETED
        )
        total_attempts = attempts.count()

        aggregates = attempts.aggregate(
            avg_score=Avg('percentage'),
            total_time=Sum('time_spent_seconds')
        )
        avg_score = round(aggregates['avg_score'] or 0, 2)
        total_time = aggregates['total_time'] or 0

        topic_stats = []
        topic_performance = QuizAttemptAnswer.objects.filter(
            attempt__in=attempts
        ).values(
            'question__question_topics__topic__name'
        ).annotate(
            total=Count('id'),
            correct=Sum(Case(When(is_correct=True, then=1), default=0, output_field=IntegerField()))
        ).exclude(
            question__question_topics__topic__name__isnull=True
        )

        for tp in topic_performance:
            t = tp['total']
            c = tp['correct']
            topic_stats.append({
                "topic": tp['question__question_topics__topic__name'],
                "total_questions": t,
                "correct": c,
                "accuracy": round((c / t * 100), 2) if t > 0 else 0
            })

        hardest = QuizAttemptAnswer.objects.filter(
            attempt__in=attempts
        ).values(
            'question__id', 'question__question_text'
        ).annotate(
            total=Count('id'),
            correct=Sum(Case(When(is_correct=True, then=1), default=0, output_field=IntegerField()))
        ).filter(total__gt=0).order_by('correct')[:5]

        hardest_questions = []
        for h in hardest:
            t = h['total']
            c = h['correct']
            hardest_questions.append({
                "question": h['question__question_text'],
                "accuracy": round((c / t * 100), 2)
            })

        return {
            "overview": {
                "total_quizzes": total_quizzes,
                "total_attempts": total_attempts,
                "average_score": avg_score,
                "total_time_spent_seconds": total_time,
            },
            "topics": topic_stats,
            "hardest_questions": hardest_questions,
        }