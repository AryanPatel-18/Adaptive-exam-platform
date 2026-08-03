from rest_framework import serializers

from processing.models import QuestionOption
from quiz.models import Quiz, QuizAttempt, QuizQuestion


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

    class Meta:
        model = QuizQuestion
        fields = (
            "order",
            "question_id",
            "question_text",
            "options",
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
        )
        read_only_fields = fields


class SubmitAnswerSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    selected_option_id = serializers.UUIDField()


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
        if obj.completed_at is None:
            return None

        return int(
            (
                obj.completed_at - obj.started_at
            ).total_seconds()
        )