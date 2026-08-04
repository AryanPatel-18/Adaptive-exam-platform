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
            QuizQuestionSerializer(question).data,
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
        )

        return Response(
            {
                "detail": "Answer submitted successfully."
            },
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