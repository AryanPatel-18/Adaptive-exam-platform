from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from common.responses import success_response
from dashboard.services import ActivityLogger

from .exceptions import AuthenticationException
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
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