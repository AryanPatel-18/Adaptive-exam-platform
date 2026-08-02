from abc import ABC, abstractmethod
from pathlib import Path

from processing.dtos import OCRResult


class BaseOCREngine(ABC):
    """
    Base class for OCR engines.
    """

    @abstractmethod
    def extract_text(
        self,
        image_path: Path,
    ) -> OCRResult:
        """
        Extract text from a preprocessed image.

        Args:
            image_path:
                Path to the preprocessed image.

        Returns:
            OCRResult containing the extracted text.
        """

        raise NotImplementedError