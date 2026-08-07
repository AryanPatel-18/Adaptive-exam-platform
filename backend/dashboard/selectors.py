from django.db import models
from django.db.models import F, ExpressionWrapper, Sum, DurationField
from django.db.models.functions import TruncDate
from django.utils import timezone
import datetime
from common.choices import WorkspaceStatus
from workspace.models import Workspace
from quiz.models import Quiz, QuizAttempt, QuizAttemptAnswer
from schedule.models import StudySchedule

class DashboardSelector:
    @staticmethod
    def get_active_workspaces_count(user):
        return Workspace.objects.filter(
            owner=user
        ).exclude(
            status=WorkspaceStatus.ARCHIVED
        ).count()

    @staticmethod
    def get_total_quizzes_taken(user):
        return QuizAttempt.objects.filter(
            user=user,
            status=QuizAttempt.Status.COMPLETED
        ).count()

    @staticmethod
    def get_average_accuracy(user):
        result = QuizAttempt.objects.filter(
            user=user,
            status=QuizAttempt.Status.COMPLETED
        ).aggregate(avg_accuracy=models.Avg('percentage'))
        return result['avg_accuracy'] or 0.0

    @staticmethod
    def get_total_questions_solved(user):
        return QuizAttemptAnswer.objects.filter(
            attempt__user=user,
            attempt__status=QuizAttempt.Status.COMPLETED,
            is_correct=True
        ).count()

    @staticmethod
    def get_total_study_time(user):
        result = QuizAttemptAnswer.objects.filter(
            attempt__user=user,
            loaded_at__isnull=False,
            answered_at__isnull=False
        ).aggregate(
            total_time=Sum(
                ExpressionWrapper(
                    F('answered_at') - F('loaded_at'), # This tells SQL to compute the information on its own
                    output_field=DurationField() # This makes sure that the return field is duration field
                )
            )
        )
        total_duration = result.get('total_time')
        return total_duration.total_seconds() if total_duration else 0.0

    @staticmethod
    def get_weekly_study_time_data(user):
        today = timezone.now().date()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        
        daily_data = []
        for i in range(7):
            target_date = start_of_week + datetime.timedelta(days=i)
            
            result = QuizAttemptAnswer.objects.filter(
                attempt__user=user,
                answered_at__date=target_date,
                loaded_at__isnull=False,
                answered_at__isnull=False
            ).aggregate(
                total_time=Sum(
                    ExpressionWrapper(
                        F('answered_at') - F('loaded_at'),
                        output_field=DurationField()
                    )
                )
            )
            total_duration = result.get('total_time')
            seconds = total_duration.total_seconds() if total_duration else 0.0
            minutes = seconds / 60.0
            
            daily_data.append(minutes)
            
        return daily_data

    @staticmethod
    def get_study_streak(user):
        active_dates = set()
        
        workspaces_dates = Workspace.objects.filter(owner=user).values_list('created_at__date', flat=True)
        quizzes_dates = Quiz.objects.filter(created_by=user).values_list('created_at__date', flat=True)
        attempts_dates = QuizAttempt.objects.filter(user=user).values_list('started_at__date', flat=True)
        answers_dates = QuizAttemptAnswer.objects.filter(attempt__user=user, answered_at__isnull=False).values_list('answered_at__date', flat=True)
        
        active_dates.update(d for d in workspaces_dates if d)
        active_dates.update(d for d in quizzes_dates if d)
        active_dates.update(d for d in attempts_dates if d)
        active_dates.update(d for d in answers_dates if d)
        
        today = timezone.now().date()
        yesterday = today - datetime.timedelta(days=1)
        
        streak = 0
        current_date = today
        
        if today in active_dates:
            streak += 1
            current_date -= datetime.timedelta(days=1)
            while current_date in active_dates:
                streak += 1
                current_date -= datetime.timedelta(days=1)
        elif yesterday in active_dates:
            current_date = yesterday
            while current_date in active_dates:
                streak += 1
                current_date -= datetime.timedelta(days=1)
                
        start_of_week = today - datetime.timedelta(days=today.weekday())
        days_completed = []
        for i in range(7):
            date = start_of_week + datetime.timedelta(days=i)
            days_completed.append(date in active_dates)
            
        return {
            "count": streak,
            "days_completed": days_completed
        }

    @staticmethod
    def get_recent_workspaces(user, limit=3):
        return Workspace.objects.filter(
            owner=user
        ).order_by('-created_at')[:limit]

    @staticmethod
    def get_recent_quizzes(user, limit=3):
        return Quiz.objects.filter(
            created_by=user
        ).order_by('-created_at')[:limit]

    @staticmethod
    def get_upcoming_schedule(user):
        today = timezone.now().date()
        return StudySchedule.objects.filter(
            user=user, 
            end_date__gte=today,
            is_active=True
        ).order_by('end_date').first()
