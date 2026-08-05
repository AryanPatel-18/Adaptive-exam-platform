from rest_framework import serializers
from workspace.models import Workspace
from files.models import File
from quiz.models import Quiz, QuizAttempt
from schedule.models import StudySchedule


class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = (
            "id",
            "title",
            "description",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "status",
            "created_at",
            "updated_at",
        )

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Workspace title cannot be empty.")

        return value


class WorkspaceDetailSerializer(WorkspaceSerializer):
    quiz_count = serializers.IntegerField(read_only=True)
    file_count = serializers.IntegerField(read_only=True)
    progress = serializers.SerializerMethodField()

    class Meta(WorkspaceSerializer.Meta):
        fields = WorkspaceSerializer.Meta.fields + (
            "quiz_count",
            "file_count",
            "progress"
        )
        
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


class UpdateWorkspaceSerializer(serializers.Serializer):
    title = serializers.CharField(
        max_length=150,
        required=False,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided for update."
            )

        return attrs

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Workspace title cannot be empty."
            )

        return value

    def validate_description(self, value):
        return value.strip()


class WorkspaceFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = (
            "id",
            "original_filename",
            "role",
            "mime_type",
            "file_size",
            "status",
            "created_at",
        )
        read_only_fields = fields