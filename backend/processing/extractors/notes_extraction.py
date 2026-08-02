import logging
from pathlib import Path

logger = logging.getLogger("processing")

from processing.validators.notes_validator import NotesValidator
from processing.ocr.base_engine import BaseOCREngine
from processing.dtos import OCRResult
from processing.ocr.pdf_converter import PDFToImageConverter
from processing.ocr.image_preprocessor import ImagePreprocessor


class NotesExtractor:
    """
    Extracts text from notes PDFs.
    """

    def __init__(
        self,
        pdf_converter: PDFToImageConverter,
        image_preprocessor: ImagePreprocessor,
        ocr_engine: BaseOCREngine,
    ) -> None:
        self._pdf_converter = pdf_converter
        self._image_preprocessor = image_preprocessor
        self._ocr_engine = ocr_engine

    def extract(
        self,
        pdf_path: Path,
        output_directory: Path,
    ) -> OCRResult:
        """
        Extract text from a notes PDF.

        Args:
            pdf_path:
                Path to the notes PDF.
            output_directory:
                Directory to store temporary page images.

        Returns:
            OCRResult containing the extracted text.
        """

        logger.info("Converting PDF '%s' to images...", pdf_path.name)
        image_paths = self._convert_pdf(
            pdf_path=pdf_path,
            output_directory=output_directory,
        )

        logger.info("Extracting text from %d pages...", len(image_paths))
        page_results = [
            self._extract_page(
                image_path=image_path,
            )
            for image_path in image_paths
        ]

        logger.info("Combining OCR results...")
        return self._combine_results(
            results=page_results,
        )

    def _convert_pdf(
        self,
        pdf_path: Path,
        output_directory: Path,
    ) -> list[Path]:
        """
        Convert the PDF into page images.
        """

        return self._pdf_converter.convert(
            pdf_path=pdf_path,
            output_directory=output_directory,
        )

    def _extract_page(
        self,
        image_path: Path,
    ) -> OCRResult:
        """
        Extract text from a single page.
        """

        logger.debug("Preprocessing image: %s", image_path.name)
        processed_image = self._image_preprocessor.preprocess(
            image_path=image_path,
        )

        logger.debug("Running OCR engine on image: %s", processed_image.name)
        result = self._ocr_engine.extract_text(
            image_path=processed_image,
        )

        logger.debug("Validating OCR result for image: %s", processed_image.name)
        NotesValidator.validate(
            result=result,
        )

        return result

    def _combine_results(
        self,
        results: list[OCRResult],
    ) -> OCRResult:
        """
        Combine OCR results from multiple pages.
        """

        return OCRResult(
            text="\n\n".join(
                result.text
                for result in results
            ),
        )