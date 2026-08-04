from decimal import Decimal

from rest_framework import serializers

from schedule.models import StudySchedule


class GenerateScheduleSerializer(serializers.Serializer):
    """
    Validates the input payload for generating
    a new study schedule.
    """

    attempt_id = serializers.UUIDField()

    study_days = serializers.IntegerField(
        min_value=1,
        max_value=90,
    )

    hours_per_day = serializers.DecimalField(
        max_digits=4,
        decimal_places=2,
        min_value=Decimal("0.50"),
        max_value=Decimal("24.00"),
    )

    start_date = serializers.DateField()


class StudyScheduleSerializer(serializers.ModelSerializer):
    """
    Serializes a StudySchedule instance for
    API responses.
    """

    class Meta:
        model = StudySchedule

        fields = [
            "id",
            "user",
            "workspace",
            "quiz_attempt",
            "preparedness_score",
            "generated_plan",
            "hours_per_day",
            "start_date",
            "end_date",
            "is_active",
            "created_at",
        ]

        read_only_fields = fields
