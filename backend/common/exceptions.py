import logging

from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Global exception handler for DRF.

    Converts every exception into a standardised JSON envelope so the
    frontend can rely on a single, predictable response shape.

    Success responses are NOT handled here – they are returned by the
    views via ``success_response()``.
    """

    # Default Exception handler
    response = exception_handler(exc, context)

    # --- Validation errors (serializer / field-level) ----------------
    if isinstance(exc, ValidationError):
        return Response(
            {
                "success": False,
                "message": "Validation failed.",
                "code": "VALIDATION_ERROR",
                "errors": exc.detail,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # --- Authentication errors ---------------------------------------
    if isinstance(exc, AuthenticationFailed):
        return Response(
            {
                "success": False,
                "message": "Authentication failed.",
                "code": getattr(exc, "default_code", "AUTHENTICATION_FAILED"),
                "errors": None,
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if isinstance(exc, NotAuthenticated):
        return Response(
            {
                "success": False,
                "message": "Authentication credentials were not provided.",
                "code": "NOT_AUTHENTICATED",
                "errors": None,
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # --- Permission errors -------------------------------------------
    if isinstance(exc, PermissionDenied):
        return Response(
            {
                "success": False,
                "message": str(exc.detail),
                "code": "PERMISSION_DENIED",
                "errors": None,
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    # --- Not found ---------------------------------------------------
    if isinstance(exc, NotFound):
        return Response(
            {
                "success": False,
                "message": str(exc.detail),
                "code": "NOT_FOUND",
                "errors": None,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # --- Method not allowed ------------------------------------------
    if isinstance(exc, MethodNotAllowed):
        return Response(
            {
                "success": False,
                "message": str(exc.detail),
                "code": "METHOD_NOT_ALLOWED",
                "errors": None,
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    # --- Any custom APIException (includes WorkspaceException tree) --
    if isinstance(exc, APIException):
        return Response(
            {
                "success": False,
                "message": str(exc.detail),
                "code": exc.default_code.upper()
                if hasattr(exc, "default_code")
                else "API_ERROR",
                "errors": None,
            },
            status=exc.status_code,
        )

    # --- Unexpected / unhandled exceptions ---------------------------
    logger.exception(
        "Unhandled exception in %s",
        context.get("view", "unknown view"),
    )

    return Response(
        {
            "success": False,
            "message": "An unexpected server error occurred.",
            "code": "INTERNAL_SERVER_ERROR",
            "errors": None,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
