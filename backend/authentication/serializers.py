from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        trim_whitespace=True
    )

    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        trim_whitespace=False,
    )

    confirm_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        trim_whitespace=False,
    )

    def validate_username(self, value):
        value = value.strip().lower()

        if not value:
            raise serializers.ValidationError(
                "Username cannot be empty."
            )

        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "Username is already taken."
            )

        return value

    def validate_email(self, value):
        value = value.lower().strip()

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "Email is already registered."
            )

        return value

    def validate_password(self, value):
        # This function would validate the password with the password settings that we have defined inside the settings.py file
        validate_password(value)
        return value

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")

        if password != confirm_password:
            raise serializers.ValidationError(
                {
                    "confirm_password": [
                        "Passwords do not match."
                    ]
                }
            )

        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "account_status",
            "created_at",
        )
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        trim_whitespace=True,
    )

    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        trim_whitespace=False,
    )

    def validate_username(self, value):
        value = value.strip().lower()

        if not value:
            raise serializers.ValidationError(
                "Username cannot be empty."
            )

        return value

class PasswordUpdateSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs.get('new_password') != attrs.get('confirm_new_password'):
            raise serializers.ValidationError({
                "confirm_new_password": ["Passwords do not match."]
            })
        return attrs