import logging

from processing.dtos import ExtractedQuestion
from processing.exceptions import EmptyExtractionException

logger = logging.getLogger("processing")


class QuestionValidator:
    """
    Validates extracted questions before they are persisted.
    """

    @staticmethod
    def validate(
        questions: list[ExtractedQuestion],
    ) -> list[ExtractedQuestion]:
        """
        Validate a collection of extracted questions.

        Args:
            questions: Collection of extracted question objects.

        Returns:
            The validated collection.

        Raises:
            EmptyExtractionException:
                If no questions were extracted.
        """
        logger.info("Validating %d extracted questions...", len(questions))

        if not questions:
            logger.error("Validation failed: No questions were extracted from the document.")
            raise EmptyExtractionException()

        logger.debug("Validation checks passed.")
        return questions