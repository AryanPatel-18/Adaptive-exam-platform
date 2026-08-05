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
from dashboard.services import ActivityLogger


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

        ActivityLogger.log(
            user=request.user,
            action="QUIZ_CREATED",
            description=f"Generated a new quiz '{quiz.title}' with {quiz.total_questions} questions.",
            metadata={"quiz_id": str(quiz.id), "workspace_id": str(quiz.workspace_id)}
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

        ActivityLogger.log(
            user=request.user,
            action="QUIZ_COMPLETED",
            description=f"Completed quiz '{attempt.quiz.title}' with score {attempt.score}%.",
            metadata={"quiz_id": str(attempt.quiz.id), "attempt_id": str(attempt.id)}
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

class QuizAttemptsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, quiz_id):
        from quiz.models import QuizAttempt
        attempts = QuizAttempt.objects.filter(
            quiz_id=quiz_id,
            user=request.user,
            status=QuizAttempt.Status.COMPLETED
        ).order_by('-completed_at')
        
        data = [
            {
                "id": str(attempt.id),
                "attempt_number": attempt.attempt_number,
                "score": attempt.score,
                "total_marks": attempt.total_marks,
                "percentage": str(attempt.percentage),
                "time_spent_seconds": attempt.time_spent_seconds,
                "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None,
            }
            for attempt in attempts
        ]
        
        return Response(data, status=status.HTTP_200_OK)

class WorkspaceQuizStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id):
        from quiz.models import Quiz, QuizAttempt, QuizAttemptAnswer
        from django.db.models import Count, Avg, Sum
        from django.db import models
        
        quizzes = Quiz.objects.filter(workspace_id=workspace_id, created_by=request.user)
        total_quizzes = quizzes.count()
        
        attempts = QuizAttempt.objects.filter(
            quiz__workspace_id=workspace_id, 
            user=request.user, 
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
            correct=Sum(models.Case(models.When(is_correct=True, then=1), default=0, output_field=models.IntegerField()))
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
            correct=Sum(models.Case(models.When(is_correct=True, then=1), default=0, output_field=models.IntegerField()))
        ).filter(total__gt=0).order_by('correct')[:5]
        
        hardest_questions = []
        for h in hardest:
            t = h['total']
            c = h['correct']
            hardest_questions.append({
                "question": h['question__question_text'],
                "accuracy": round((c / t * 100), 2)
            })

        return Response({
            "overview": {
                "total_quizzes": total_quizzes,
                "total_attempts": total_attempts,
                "average_score": avg_score,
                "total_time_spent_seconds": total_time,
            },
            "topics": topic_stats,
            "hardest_questions": hardest_questions
        }, status=status.HTTP_200_OK)