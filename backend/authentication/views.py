from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from common.responses import success_response
from dashboard.services import ActivityLogger

from .exceptions import AuthenticationException
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer, PasswordUpdateSerializer
from .services import AuthenticationService


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = AuthenticationService.register_user(serializer.validated_data)

        except AuthenticationException as exc:
            raise exc

        return success_response(
            message="User registered successfully.",
            data={
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
            },
            status_code=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        authentication_data = AuthenticationService.authenticate_user(
            serializer.validated_data
        )
        
        user = authentication_data["user"]
        ActivityLogger.log(
            user=user,
            action="LOGIN",
            description="User logged into the platform."
        )

        return success_response(
            message="Login successful.",
            data={
                "access": authentication_data["access"],
                "refresh": authentication_data["refresh"],
                "user": UserSerializer(
                    authentication_data["user"]
                ).data,
            },
            status_code=status.HTTP_200_OK,
        )


class UserProfileView(APIView):
    """
    Retrieve the authenticated user's profile information.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        
        return success_response(
            message="User profile retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )


class UpdatePasswordView(APIView):
    """
    Allow authenticated user to update their password.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            AuthenticationService.update_password(request.user, serializer.validated_data)
        except AuthenticationException as exc:
            raise exc
        
        ActivityLogger.log(
            user=request.user,
            action="PASSWORD_UPDATED",
            description="User updated their password."
        )

        return success_response(
            message="Password updated successfully.",
            data=None,
            status_code=status.HTTP_200_OK,
        )