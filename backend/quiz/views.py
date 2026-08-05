from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from quiz.selectors import AttemptSelector
from quiz.serializers import (
    CreateQuizSerializer,
    QuizQuestionSerializer,
    QuizResultSerializer,
    QuizSerializer,
    StartQuizSerializer,
    SubmitAnswerSerializer,
    PauseQuizSerializer,
)
from quiz.services import (
    QuizAttemptService,
    QuizGenerationService,
)


class CreateQuizAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateQuizSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quiz = QuizGenerationService.create_quiz(
            workspace_id=serializer.validated_data["workspace_id"],
            created_by=request.user,
            title=serializer.validated_data["title"],
            question_count=serializer.validated_data["question_count"],
        )

        return Response(
            QuizSerializer(quiz).data,
            status=status.HTTP_201_CREATED,
        )


class StartQuizAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, quiz_id):
        attempt = QuizAttemptService.start_attempt(
            quiz_id=quiz_id,
            user=request.user,
        )

        return Response(
            StartQuizSerializer(attempt).data,
            status=status.HTTP_201_CREATED,
        )


class ResumeQuizAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, quiz_id):
        attempt = QuizAttemptService.resume_attempt(
            quiz_id=quiz_id,
            user=request.user,
        )

        return Response(
            StartQuizSerializer(attempt).data,
            status=status.HTTP_200_OK,
        )


class QuizQuestionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id, question_order):
        attempt = AttemptSelector.get_attempt_for_user(
            attempt_id=attempt_id,
            user=request.user,
        )

        question = QuizAttemptService.get_question(
            attempt=attempt,
            question_order=question_order,
        )

        return Response(
            QuizQuestionSerializer(question, context={"attempt": attempt}).data,
            status=status.HTTP_200_OK,
        )


class SubmitAnswerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, attempt_id):
        serializer = SubmitAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attempt = AttemptSelector.get_attempt_for_user(
            attempt_id=attempt_id,
            user=request.user,
        )

        QuizAttemptService.submit_answer(
            attempt=attempt,
            question_id=serializer.validated_data["question_id"],
            selected_option_id=serializer.validated_data["selected_option_id"],
            time_spent_seconds=serializer.validated_data.get("time_spent_seconds", 0),
        )

        return Response(
            {
                "detail": "Answer submitted successfully."
            },
            status=status.HTTP_200_OK,
        )

class PauseQuizAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, attempt_id):
        serializer = PauseQuizSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attempt = AttemptSelector.get_attempt_for_user(
            attempt_id=attempt_id,
            user=request.user,
        )

        QuizAttemptService.pause_attempt(
            attempt=attempt,
            time_spent_seconds=serializer.validated_data.get("time_spent_seconds", 0),
        )

        return Response(
            {"detail": "Time saved successfully."},
            status=status.HTTP_200_OK,
        )


class FinishQuizAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, attempt_id):
        attempt = AttemptSelector.get_attempt_for_user(
            attempt_id=attempt_id,
            user=request.user,
        )

        attempt = QuizAttemptService.finish_attempt(
            attempt=attempt,
        )

        return Response(
            QuizResultSerializer(attempt).data,
            status=status.HTTP_200_OK,
        )


class QuizResultAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id):
        attempt = AttemptSelector.get_attempt_for_user(
            attempt_id=attempt_id,
            user=request.user,
        )

        return Response(
            QuizResultSerializer(attempt).data,
            status=status.HTTP_200_OK,
        )


class UserQuizAttemptsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from quiz.models import QuizAttempt
        attempts = QuizAttempt.objects.filter(
            user=request.user
        ).select_related('quiz').order_by('created_at')
        
        data = [
            {
                "id": str(attempt.id),
                "created_at": attempt.created_at.isoformat(),
                "number_of_questions": attempt.quiz.total_questions,
            }
            for attempt in attempts
        ]
        
        return Response(data, status=status.HTTP_200_OK)


class AttemptableQuizzesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id):
        from quiz.models import Quiz
        from django.db.models import Count
        
        quizzes = Quiz.objects.filter(
            workspace_id=workspace_id,
            created_by=request.user
        ).annotate(
            actual_question_count=Count('quiz_questions')
        ).filter(
            actual_question_count__gt=0
        ).order_by('-created_at')
        
        data = [
            {
                "id": str(quiz.id),
                "title": quiz.title,
                "total_questions": quiz.total_questions,
                "actual_question_count": quiz.actual_question_count,
                "created_at": quiz.created_at.isoformat(),
            }
            for quiz in quizzes
        ]
        
        return Response(data, status=status.HTTP_200_OK)

class InProgressQuizzesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id):
        from quiz.models import QuizAttempt
        attempts = QuizAttempt.objects.filter(
            quiz__workspace_id=workspace_id,
            user=request.user,
            status=QuizAttempt.Status.IN_PROGRESS
        ).select_related('quiz').order_by('-updated_at')
        
        data = [
            {
                "id": str(attempt.quiz.id),
                "title": attempt.quiz.title,
                "total_questions": attempt.quiz.total_questions,
                "attempt_id": str(attempt.id),
                "attempt_number": attempt.attempt_number,
                "started_at": attempt.started_at.isoformat(),
            }
            for attempt in attempts
        ]
        
        return Response(data, status=status.HTTP_200_OK)