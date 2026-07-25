from rest_framework import status
from rest_framework.exceptions import APIException


class ProcessingException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Processing failed."
    default_code = "processing_failed"


class InvalidQuestionException(ProcessingException):
    default_detail = "The extracted questions are invalid."
    default_code = "invalid_questions"


class EmptyExtractionException(ProcessingException):
    default_detail = "No questions were extracted."
    default_code = "empty_extraction"


class DownloadFailedException(ProcessingException):
    default_detail = "Failed to download the source file."
    default_code = "download_failed"


class ExtractionFailedException(ProcessingException):
    default_detail = "Failed to extract questions from the file."
    default_code = "extraction_failed"