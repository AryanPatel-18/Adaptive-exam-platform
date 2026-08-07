from rest_framework import serializers

from processing.models import QuestionOption
from quiz.models import Quiz, QuizAttempt, QuizQuestion, QuizAttemptAnswer


class CreateQuizSerializer(serializers.Serializer):
    workspace_id = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    question_count = serializers.IntegerField(
        min_value=1,
        max_value=50,
    )


class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = (
            "id",
            "title",
            "total_questions",
            "created_at",
        )
        read_only_fields = fields


class QuizQuestionSerializer(serializers.ModelSerializer):
    question_id = serializers.SerializerMethodField()
    question_text = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()
    selected_option_id = serializers.SerializerMethodField()

    class Meta:
        model = QuizQuestion
        fields = (
            "order",
            "question_id",
            "question_text",
            "options",
            "selected_option_id",
        )

    def get_question_id(self, obj):
        return str(obj.question.id)

    def get_question_text(self, obj):
        return obj.question.question_text

    def get_options(self, obj):
        return QuestionOptionSerializer(
            obj.question.options.all(),
            many=True,
        ).data

    def get_selected_option_id(self, obj):
        attempt = self.context.get("attempt")
        if not attempt:
            return None
        answer = QuizAttemptAnswer.objects.filter(
            attempt=attempt,
            question=obj.question
        ).first()
        if answer and answer.selected_option_id:
            return str(answer.selected_option_id)
        return None


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = (
            "id",
            "text",
        )
        read_only_fields = fields


class StartQuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = (
            "id",
            "attempt_number",
            "started_at",
            "time_spent_seconds",
        )
        read_only_fields = fields


class SubmitAnswerSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    selected_option_id = serializers.UUIDField()
    time_spent_seconds = serializers.IntegerField(min_value=0, default=0)

class PauseQuizSerializer(serializers.Serializer):
    time_spent_seconds = serializers.IntegerField(min_value=0, default=0)


class QuizResultSerializer(serializers.ModelSerializer):
    time_taken_seconds = serializers.SerializerMethodField()

    class Meta:
        model = QuizAttempt
        fields = (
            "score",
            "correct_answers",
            "wrong_answers",
            "percentage",
            "time_taken_seconds",
            "completed_at",
        )
        read_only_fields = fields

    def get_time_taken_seconds(self, obj):
        return obj.time_spent_seconds


class OverviewStatsSerializer(serializers.Serializer):
    total_quizzes = serializers.IntegerField()
    total_attempts = serializers.IntegerField()
    average_score = serializers.FloatField()
    total_time_spent_seconds = serializers.IntegerField()


class TopicPerformanceStatsSerializer(serializers.Serializer):
    topic = serializers.CharField()
    total_questions = serializers.IntegerField()
    correct = serializers.IntegerField()
    accuracy = serializers.FloatField()


class HardestQuestionStatsSerializer(serializers.Serializer):
    question = serializers.CharField()
    accuracy = serializers.FloatField()


class WorkspaceQuizStatsSerializer(serializers.Serializer):
    overview = OverviewStatsSerializer()
    topics = TopicPerformanceStatsSerializer(many=True)
    hardest_questions = HardestQuestionStatsSerializer(many=True)