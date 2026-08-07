from django.contrib.auth import get_user_model, authenticate
from django.db import IntegrityError, DatabaseError, transaction
from wallet.services import WalletService
from rest_framework_simplejwt.tokens import RefreshToken
import logging

from .exceptions import UserRegistrationException, InvalidCredentialsException, InactiveAccountException

User = get_user_model()
logger = logging.getLogger("authentication")

# This class is created to provide services for the authentication
class AuthenticationService:
    @staticmethod
    @transaction.atomic
    def register_user(validated_data):
        data = validated_data.copy()
        data.pop("confirm_password")
        try:
            user = User.objects.create_user(**data)
            WalletService.create_wallet(user)
            logger.info("Successfully registered user: %s", user.username)
            return user
        except IntegrityError:
            logger.warning("Registration failed: Username or email already exists (username: %s)", data.get("username"))
            raise UserRegistrationException(
                detail="A user with the provided username or email already exists."
            )
        except DatabaseError as e:
            logger.error("Database error during user registration for username: %s - %s", data.get("username"), e, exc_info=True)
            raise UserRegistrationException(
                detail="Failed to create user."
            )
    @staticmethod
    def authenticate_user(validated_data):
        username = validated_data["username"]
        password = validated_data["password"]

        user = authenticate(
            username=username,
            password=password,
        )

        if user is None:
            logger.warning("Authentication failed: Invalid credentials for username: %s", username)
            raise InvalidCredentialsException()

        if not user.is_active:
            logger.warning("Authentication failed: Inactive account for username: %s", username)
            raise InactiveAccountException()

        refresh = RefreshToken.for_user(user)
        logger.info("User successfully authenticated: %s", username)

        return {
            "user": user,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    @staticmethod
    def update_password(user, validated_data):
        current_password = validated_data["current_password"]
        new_password = validated_data["new_password"]

        if not user.check_password(current_password):
            logger.warning("Password update failed: Incorrect current password for username: %s", user.username)
            raise InvalidCredentialsException(detail="Incorrect current password.")

        user.set_password(new_password)
        user.save()
        logger.info("User successfully updated password: %s", user.username)
        return user