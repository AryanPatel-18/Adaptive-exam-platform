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


class PDFConversionException(ProcessingException):
    default_detail = "Failed to convert PDF file."
    default_code = "pdf_conversion_failed"


class ImagePreprocessingException(ProcessingException):
    default_detail = "Failed to preprocess image."
    default_code = "image_preprocessing_failed"


class OCRException(ProcessingException):
    default_detail = "OCR extraction failed."
    default_code = "ocr_failed"


class NotesValidationException(ProcessingException):
    default_detail = "Validation of uploaded notes failed."
    default_code = "notes_validation_failed"


class TopicValidationException(ProcessingException):
    default_detail = "Validation of extracted topics failed."
    default_code = "topic_validation_failed"