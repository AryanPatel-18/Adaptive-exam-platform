from rest_framework import serializers
from workspace.models import Workspace
from quiz.models import Quiz, QuizAttempt
from schedule.models import StudySchedule

class RecentWorkspaceSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = ['id', 'title', 'status', 'created_at', 'progress']

    def get_progress(self, obj):
        progress = 0
        if obj.status in ['PROCESSING', 'READY_FOR_PROCESSING']:
            progress = max(progress, 20)
        if obj.status == 'READY':
            progress = max(progress, 40)
            
        if Quiz.objects.filter(workspace=obj).exists():
            progress = max(progress, 60)
            
        if QuizAttempt.objects.filter(quiz__workspace=obj, status=QuizAttempt.Status.COMPLETED).exists():
            progress = max(progress, 80)
            
        if StudySchedule.objects.filter(workspace=obj).exists():
            progress = max(progress, 100)
            
        return progress

class RecentQuizSerializer(serializers.ModelSerializer):
    attempted_questions = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'total_questions', 'created_at', 'attempted_questions', 'score', 'workspace']

    def _get_latest_attempt(self, obj):
        user = self.context.get('request').user if self.context.get('request') else obj.created_by
        return obj.attempts.filter(user=user).order_by('-started_at').first()

    def get_attempted_questions(self, obj):
        attempt = self._get_latest_attempt(obj)
        if attempt:
            return attempt.correct_answers + attempt.wrong_answers
        return 0

    def get_score(self, obj):
        attempt = self._get_latest_attempt(obj)
        if attempt:
            return float(attempt.percentage)
        return 0.0

class StudyStreakSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    days_completed = serializers.ListField(
        child=serializers.BooleanField()
    )

class UpcomingScheduleSerializer(serializers.ModelSerializer):
    subject = serializers.CharField(source='workspace.title')
    timing = serializers.SerializerMethodField()
    timingColor = serializers.SerializerMethodField()

    class Meta:
        model = StudySchedule
        fields = ['id', 'subject', 'timing', 'timingColor']

    def get_timing(self, obj):
        return f"{obj.start_date.strftime('%b %d')} - {obj.end_date.strftime('%b %d')}"

    def get_timingColor(self, obj):
        return '#7c3aed'

class DashboardStatsSerializer(serializers.Serializer):
    active_workspaces = serializers.IntegerField()
    total_quizzes_taken = serializers.IntegerField()
    average_accuracy = serializers.FloatField()
    questions_solved = serializers.IntegerField()
    total_study_time = serializers.FloatField()
    study_streak = StudyStreakSerializer()
    recent_workspaces = RecentWorkspaceSerializer(many=True)
    recent_quizzes = RecentQuizSerializer(many=True)
    upcoming_revision = UpcomingScheduleSerializer(allow_null=True)

class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        from dashboard.models import UserActivity
        model = UserActivity
        fields = ['id', 'action', 'description', 'metadata', 'timestamp']
