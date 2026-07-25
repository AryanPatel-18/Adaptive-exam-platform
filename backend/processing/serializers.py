from rest_framework import serializers


class ProcessFileSerializer(serializers.Serializer):
    file_id = serializers.UUIDField()