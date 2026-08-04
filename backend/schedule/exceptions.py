from rest_framework.exceptions import APIException


class ScheduleException(APIException):
    status_code = 400
    default_detail = "A study schedule operation failed."
    default_code = "schedule_error"


class ScheduleNotFoundException(ScheduleException):
    status_code = 404
    default_detail = "The requested study schedule does not exist."
    default_code = "schedule_not_found"


class ScheduleGenerationFailedException(ScheduleException):
    status_code = 502
    default_detail = "Failed to generate study schedule. Please try again."
    default_code = "schedule_generation_failed"


class WorkspaceNotFoundException(ScheduleException):
    status_code = 404
    default_detail = "The requested workspace does not exist."
    default_code = "workspace_not_found"
