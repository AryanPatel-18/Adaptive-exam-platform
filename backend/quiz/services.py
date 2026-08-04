import random

from django.db import transaction
from django.utils import timezone

from processing.models import QuestionOption
from quiz.exceptions import (
    InvalidQuestionOrderException,
    NoQuestionsAvailableException,
    QuestionAlreadyAnsweredException,
    QuizAlreadyCompletedException,
    InvalidQuizSubmissionException,
)
from quiz.models import Quiz, QuizQuestion, QuizAttempt, QuizAttemptAnswer
from quiz.selectors import (
    QuestionSelector,
    WorkspaceSelector,
    AttemptSelector,
    QuizSelector,
    AttemptAnswerSelector,
)


class QuizGenerationService:
    """
    Responsible for generating quizzes from processed questions.
    """

    @staticmethod
    @transaction.atomic
    def create_quiz(
        *,
        workspace_id,
        created_by,
        title,
        question_count,
    ):
        workspace = WorkspaceSelector.get_workspace_for_user(
            workspace_id=workspace_id,
            user=created_by,
        )

        questions = list(
            QuestionSelector.get_questions_for_workspace(
                workspace=workspace,
            )
        )

        random.shuffle(questions)

        selected_questions = questions[: min(question_count, 50)]

        if not selected_questions:
            raise NoQuestionsAvailableException()

        quiz = Quiz.objects.create(
            workspace=workspace,
            created_by=created_by,
            title=title,
            total_questions=len(selected_questions),
        )

        QuizQuestion.objects.bulk_create(
            [
                QuizQuestion(
                    quiz=quiz,
                    question=question,
                    order=index,
                )
                for index, question in enumerate(
                    selected_questions,
                    start=1,
                )
            ]
        )

        return quiz

class QuizAttemptService:
    """
    Responsible for the complete quiz attempt lifecycle.
    """

    @staticmethod
    @transaction.atomic
    def start_attempt(
        *,
        quiz_id,
        user,
    ):
        quiz = QuizSelector.get_quiz_for_user(
            quiz_id=quiz_id,
            user=user,
        )

        latest_attempt = AttemptSelector.get_latest_attempt(
            quiz=quiz,
            user=user,
        )

        attempt_number = (
            1
            if latest_attempt is None
            else latest_attempt.attempt_number + 1
        )

        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=user,
            attempt_number=attempt_number,
        )

        return attempt

    @staticmethod
    def get_question(
        *,
        attempt,
        question_order,
    ):
        if question_order < 1 or question_order > attempt.quiz.total_questions:
            raise InvalidQuestionOrderException()

        quiz_question = QuestionSelector.get_question_by_order(
            quiz=attempt.quiz,
            order=question_order,
        )

        if AttemptAnswerSelector.question_answered(
            attempt=attempt,
            question=quiz_question.question,
        ):
            raise QuestionAlreadyAnsweredException()

        # Record loaded_at when the question is first retrieved
        QuizAttemptAnswer.objects.get_or_create(
            attempt=attempt,
            question=quiz_question.question,
            defaults={
                "loaded_at": timezone.now(),
            },
        )

        return quiz_question

    @staticmethod
    @transaction.atomic
    def submit_answer(
        *,
        attempt,
        question_id,
        selected_option_id,
    ):
        if attempt.status == attempt.Status.COMPLETED:
            raise QuizAlreadyCompletedException()

        if attempt.status != attempt.Status.IN_PROGRESS:
            raise InvalidQuizSubmissionException()

        try:
            quiz_question = QuizQuestion.objects.select_related(
                "question",
            ).get(
                quiz=attempt.quiz,
                question_id=question_id,
            )
        except QuizQuestion.DoesNotExist:
            raise InvalidQuizSubmissionException()

        existing_answer = AttemptAnswerSelector.get_attempt_answer(
            attempt=attempt,
            question=quiz_question.question,
        )

        if existing_answer is not None and existing_answer.answered_at is not None:
            raise QuestionAlreadyAnsweredException()

        # If no answer record exists (question was never loaded via get_question),
        # create one now as a fallback.
        if existing_answer is None:
            existing_answer = QuizAttemptAnswer.objects.create(
                attempt=attempt,
                question=quiz_question.question,
                loaded_at=timezone.now(),
            )

        try:
            selected_option = QuestionOption.objects.get(
                id=selected_option_id,
                question=quiz_question.question,
            )
        except QuestionOption.DoesNotExist:
            raise InvalidQuizSubmissionException()

        existing_answer.selected_option = selected_option
        existing_answer.answered_at = timezone.now()
        existing_answer.is_correct = selected_option.is_correct
        existing_answer.save(
            update_fields=[
                "selected_option",
                "answered_at",
                "is_correct",
                "updated_at",
            ]
        )

        return existing_answer

    @staticmethod
    @transaction.atomic
    def finish_attempt(
        *,
        attempt,
    ):
        if attempt.status == attempt.Status.COMPLETED:
            raise QuizAlreadyCompletedException()

        if attempt.status != attempt.Status.IN_PROGRESS:
            raise InvalidQuizSubmissionException()

        score_data = QuizAttemptService.calculate_score(
            attempt=attempt,
        )

        attempt.correct_answers = score_data["correct_answers"]
        attempt.wrong_answers = score_data["wrong_answers"]
        attempt.score = score_data["score"]
        attempt.total_marks = score_data["total_marks"]
        attempt.percentage = score_data["percentage"]
        attempt.completed_at = timezone.now()
        attempt.status = QuizAttempt.Status.COMPLETED

        attempt.save(
            update_fields=[
                "correct_answers",
                "wrong_answers",
                "score",
                "total_marks",
                "percentage",
                "completed_at",
                "status",
                "updated_at",
            ]
        )

        return attempt

    @staticmethod
    def calculate_score(
        *,
        attempt,
    ):
        answers = QuizAttemptAnswer.objects.filter(
            attempt=attempt,
            answered_at__isnull=False,
        )

        correct_answers = answers.filter(
            is_correct=True,
        ).count()

        wrong_answers = answers.filter(
            is_correct=False,
        ).count()

        total_marks = attempt.quiz.total_questions

        score = correct_answers

        percentage = (
            round((score / total_marks) * 100, 2)
            if total_marks > 0
            else 0
        )

        return {
            "score": score,
            "total_marks": total_marks,
            "correct_answers": correct_answers,
            "wrong_answers": wrong_answers,
            "percentage": percentage,
        }