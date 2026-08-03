import logging
from pathlib import Path

import easyocr
import numpy as np

from processing.ocr.base_engine import BaseOCREngine
from processing.dtos import OCRResult
from processing.exceptions import OCRException

logger = logging.getLogger("processing")

MIN_OCR_CONFIDENCE = 0.3


class EasyOCREngine(BaseOCREngine):
    """
    OCR engine implementation using EasyOCR.

    Supports both file path and in-memory numpy array input.
    Includes confidence filtering to discard low-quality detections.
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

        self._gpu = self._detect_gpu()

        self._reader = easyocr.Reader(
            lang_list=languages or ["en"],
            gpu=self._gpu,
        )

    @staticmethod
    def _detect_gpu() -> bool:
        """Return True if a CUDA-capable GPU is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def extract_text(
        self,
        image_path: Path,
    ) -> OCRResult:
        """
        Extract text from a preprocessed image file.

        Args:
            image_path:
                Path to the preprocessed image.

        Returns:
            OCRResult containing the extracted text and confidence.

        Raises:
            OCRException:
                If text extraction fails.
        """

        self._validate_image(
            image_path=image_path,
        )

        logger.debug("Starting EasyOCR extraction for image: %s", image_path.name)
        detections = self._read_text_from_path(
            image_path=image_path,
        )

        logger.debug("EasyOCR completed. Building result for image: %s", image_path.name)
        return self._build_result(
            detections=detections,
        )

    def extract_text_from_array(
        self,
        image: np.ndarray,
    ) -> OCRResult:
        """
        Extract text from an in-memory numpy array.

        Args:
            image:
                Numpy array (grayscale or RGB).

        Returns:
            OCRResult containing the extracted text and confidence.

        Raises:
            OCRException:
                If text extraction fails.
        """

        logger.debug("Starting EasyOCR extraction from numpy array...")
        detections = self._read_text_from_array(
            image=image,
        )

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

    def _read_text_from_path(
        self,
        image_path: Path,
    ) -> list:
        """
        Perform OCR on an image file.

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

    def _read_text_from_array(
        self,
        image: np.ndarray,
    ) -> list:
        """
        Perform OCR on an in-memory numpy array.

        Args:
            image:
                Numpy array (grayscale or RGB).

        Returns:
            Raw EasyOCR output.

        Raises:
            OCRException:
                If OCR extraction fails.
        """

        try:
            return self._reader.readtext(
                image,
                detail=1,
                paragraph=False,
            )

        except Exception as exception:
            logger.error("EasyOCR failed to extract text from array: %s", exception)
            raise OCRException(
                "Failed to extract text from image array."
            ) from exception

    def _build_result(
        self,
        detections: list,
    ) -> OCRResult:
        """
        Convert EasyOCR output into an OCRResult with confidence filtering.

        Detections below MIN_OCR_CONFIDENCE are discarded.

        Args:
            detections:
                Raw output from EasyOCR.

        Returns:
            OCRResult containing the extracted text and average confidence.
        """
        logger.debug("Building OCR result from %d detections...", len(detections))
        texts = []
        scores = []

        for detection in detections:
            if not detection or len(detection) < 3:
                continue

            text = str(detection[1]).strip()
            confidence = float(detection[2])

            if not text:
                continue

            if confidence < MIN_OCR_CONFIDENCE:
                continue

            texts.append(text)
            scores.append(confidence)

        if not texts:
            return OCRResult(text="", confidence=0.0)

        full_text = "\n".join(texts)
        avg_confidence = sum(scores) / len(scores)

        logger.info(
            "OCR extracted %d text blocks with average confidence %.2f",
            len(texts),
            avg_confidence,
        )

        return OCRResult(
            text=full_text,
            confidence=avg_confidence,
        )