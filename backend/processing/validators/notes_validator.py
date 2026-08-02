from processing.dtos import OCRResult
from processing.exceptions import NotesValidationException


class NotesValidator:
    """
    Validates OCR results extracted from notes.
    """

    MIN_TEXT_LENGTH = 50

    @classmethod
    def validate(
        cls,
        result: OCRResult,
    ) -> None:
        """
        Validate the extracted OCR text.

        Args:
            result:
                OCR result produced by the OCR engine.

        Raises:
            NotesValidationException:
                If the extracted text is not suitable for further processing.
        """

        text = result.text.strip()

        if not text:
            raise NotesValidationException(
                "No text could be extracted from the uploaded notes."
            )

        if len(text) < cls.MIN_TEXT_LENGTH:
            raise NotesValidationException(
                "The extracted text is too short to process."
            )

        if len(text.split()) < 10:
            raise NotesValidationException(
                "The uploaded notes do not contain enough readable text."
            )