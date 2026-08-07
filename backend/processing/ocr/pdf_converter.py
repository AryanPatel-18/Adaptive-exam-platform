import logging
from pathlib import Path

import fitz  # PyMuPDF

from processing.exceptions import PDFConversionException

logger = logging.getLogger("processing")


class PDFToImageConverter:
    """
    Converts PDF pages to images using PyMuPDF.

    Also exposes direct access to PyMuPDF Page objects for
    structured text extraction (used by NotesExtractor for
    direct-text-first strategy).
    """

    IMAGE_EXTENSION = ".png"
    OCR_ZOOM = 3.0 # Resolution Multiplier

    def convert(
        self,
        pdf_path: Path,
        output_directory: Path,
    ) -> list[Path]:
        """
        Convert all PDF pages to images.

        Args:
            pdf_path: Path to the PDF file.
            output_directory: Directory to save page images.

        Returns:
            List of paths to saved page images.
        """

        logger.debug("Converting PDF '%s' to images...", pdf_path.name)
        document = self._open_pdf(pdf_path)
        image_paths: list[Path] = []

        try:
            for page_number, page in enumerate(document, start=1):
                logger.debug("Rendering page %d...", page_number)
                pixmap = self._render_page(page)

                output_path = self._generate_output_path(
                    output_directory=output_directory,
                    page_number=page_number,
                )

                image_paths.append(
                    self._save_page(
                        pixmap=pixmap,
                        output_path=output_path,
                    )
                )

        finally:
            document.close()

        logger.debug("Successfully converted %d pages from PDF.", len(image_paths))
        return image_paths

    def open_document(
        self,
        pdf_path: Path,
    ) -> fitz.Document:
        """
        Open a PDF document and return it for direct page access.

        The caller is responsible for closing the document.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            An opened PyMuPDF document.
        """

        return self._open_pdf(pdf_path)

    def _open_pdf(
        self,
        pdf_path: Path,
    ) -> fitz.Document:
        """
        Open a PDF document for page rendering.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            An opened PyMuPDF document.

        Raises:
            PDFConversionException:
                If the file cannot be opened.
        """

        if not pdf_path.exists():
            logger.error("PDF file not found: %s", pdf_path)
            raise PDFConversionException(
                detail=f"PDF file not found: '{pdf_path}'."
            )

        try:
            return fitz.open(str(pdf_path))

        except Exception as exc:
            logger.error("Failed to open PDF '%s': %s", pdf_path.name, exc)
            raise PDFConversionException(
                detail=f"Failed to open PDF: '{pdf_path.name}'."
            ) from exc

    def _save_page(
        self,
        pixmap: fitz.Pixmap,
        output_path: Path,
    ) -> Path:
        """
        Save a rendered PDF page as an image.

        Args:
            pixmap: Rendered page.
            output_path: Destination image path.

        Returns:
            Path to the saved image.

        Raises:
            PDFConversionException:
                If the image cannot be written.
        """

        try:
            pixmap.save(output_path)
            return output_path

        except Exception as exc:
            logger.error("Failed to save rendered page '%s': %s", output_path.name, exc)
            raise PDFConversionException(
                detail=f"Failed to save rendered page '{output_path.name}'."
            ) from exc

    def _generate_output_path(
        self,
        output_directory: Path,
        page_number: int,
    ) -> Path:
        """
        Generate the output path for a rendered PDF page.

        Args:
            output_directory: Directory where images will be stored.
            page_number: 1-based page number.

        Returns:
            The full path to the output image.
        """

        filename = f"page_{page_number}{self.IMAGE_EXTENSION}"
        return output_directory / filename

    def _render_page(
        self,
        page: fitz.Page,
    ) -> fitz.Pixmap:
        """
        Render a PDF page into a high-resolution image.

        Uses OCR_ZOOM (3.0x) matching the test file's approach.

        Args:
            page: PDF page to render.

        Returns:
            Rendered page as a Pixmap.

        Raises:
            PDFConversionException:
                If the page cannot be rendered.
        """

        try:
            matrix = fitz.Matrix(
                self.OCR_ZOOM,
                self.OCR_ZOOM,
            )

            return page.get_pixmap(
                matrix=matrix,
                alpha=False,
            )

        except Exception as exc:
            logger.error("Failed to render page %d: %s", page.number + 1, exc)
            raise PDFConversionException(
                detail=f"Failed to render page {page.number + 1}."
            ) from exc