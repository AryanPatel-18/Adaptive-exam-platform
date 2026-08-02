import logging
from pathlib import Path

logger = logging.getLogger("processing")

import easyocr

from processing.ocr.base_engine import BaseOCREngine
from processing.dtos import OCRResult
from processing.exceptions import OCRException


class EasyOCREngine(BaseOCREngine):
    """
    OCR engine implementation using EasyOCR.
    """

    def __init__(
        self,
        languages: list[str] | None = None,
    ) -> None:
        """
        Initialize the EasyOCR engine.

        Args:
            languages:
                Languages supported by the OCR engine.
                Defaults to English.
        """

        self._reader = easyocr.Reader(
            lang_list=languages or ["en"],
            gpu=True,
        )

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

        Raises:
            OCRException:
                If text extraction fails.
        """

        self._validate_image(
            image_path=image_path,
        )

        logger.debug("Starting EasyOCR extraction for image: %s", image_path.name)
        detections = self._read_text(
            image_path=image_path,
        )

        logger.debug("EasyOCR completed. Building result for image: %s", image_path.name)
        return self._build_result(
            detections=detections,
        )

    def _validate_image(
        self,
        image_path: Path,
    ) -> None:
        """
        Validate the input image.

        Args:
            image_path:
                Path to the image.

        Raises:
            OCRException:
                If the image is invalid.
        """

        if not image_path.exists():
            logger.error("Image does not exist: %s", image_path)
            raise OCRException(
                f"Image does not exist: {image_path}"
            )

        if not image_path.is_file():
            logger.error("Expected a file but received: %s", image_path)
            raise OCRException(
                f"Expected a file but received: {image_path}"
            )

        if image_path.suffix.lower() not in {
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".tiff",
            ".tif",
        }:
            logger.error("Unsupported image format: %s", image_path.suffix)
            raise OCRException(
                f"Unsupported image format: {image_path.suffix}"
            )

    def _read_text(
        self,
        image_path: Path,
    ) -> list:
        """
        Perform OCR using EasyOCR.

        Args:
            image_path:
                Path to the preprocessed image.

        Returns:
            Raw EasyOCR output.

        Raises:
            OCRException:
                If OCR extraction fails.
        """

        try:
            return self._reader.readtext(
                str(image_path),
                detail=1,
                paragraph=False,
            )

        except Exception as exception:
            logger.error("EasyOCR failed to extract text from image '%s': %s", image_path.name, exception)
            raise OCRException(
                f"Failed to extract text from image: {image_path}"
            ) from exception

    def _build_result(
        self,
        detections: list,
    ) -> OCRResult:
        """
        Convert EasyOCR output into an OCRResult.

        Args:
            detections:
                Raw output from EasyOCR.

        Returns:
            OCRResult containing the extracted text.
        """

        text = "\n".join(
            detection[1]
            for detection in detections
        )

        return OCRResult(
            text=text,
        )