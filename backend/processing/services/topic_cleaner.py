"""
Topic cleaner service.

Uses Ollama per-page cleaning to extract conceptual headings
from OCR text, replacing the naive regex-based TopicExtractor.

Logic ported from tests/Extraction Files Testing/hand_notes_extraction.py
(lines 866-892).
"""

import logging

from processing.dtos import NotesExtractionResult
from processing.prompts import PROMPT_TEMPLATE_CLEAN_PAGE
from processing.services.ollama_client import (
    OllamaClient,
    OLLAMA_MODEL_CLEAN,
)
from processing.extractors.notes_extraction import unique_preserve_order

logger = logging.getLogger("processing")


class TopicCleaner:
    """
    Cleans and extracts conceptual headings from notes
    extraction results using Ollama per-page cleaning.

    Falls back to heuristic-detected headings if Ollama
    is offline or fails.
    """

    @staticmethod
    def clean(
        extraction_result: NotesExtractionResult,
    ) -> list[str]:
        """
        Extract cleaned candidate headings from all pages.

        For each page, sends the OCR text to Ollama 1.7b to extract
        conceptual topics. Falls back to heuristic headings on failure.

        Args:
            extraction_result:
                The NotesExtractionResult from the notes extractor.

        Returns:
            A deduplicated list of candidate headings across all pages,
            preserving document order.
        """

        all_headings: list[str] = []

        if OllamaClient.check_status():
            logger.info(
                "Ollama is online. Running per-page cleaning with model '%s'...",
                OLLAMA_MODEL_CLEAN,
            )

            OllamaClient.load_model(OLLAMA_MODEL_CLEAN)

            try:
                for page in extraction_result.pages:
                    page_text = page.content
                    if not page_text:
                        continue

                    page_headings = TopicCleaner._clean_page_with_ollama(
                        page_number=page.page,
                        page_text=page_text,
                        fallback_headings=page.headings,
                    )

                    # Update the page's headings with cleaned ones
                    page.headings = page_headings
                    all_headings.extend(page_headings)

            finally:
                OllamaClient.unload_model(OLLAMA_MODEL_CLEAN)
        else:
            logger.warning(
                "Ollama service offline. Falling back to heuristic headings."
            )

            for page in extraction_result.pages:
                all_headings.extend(page.headings)

        candidate_headings = unique_preserve_order(all_headings)

        logger.info(
            "Topic cleaning complete. %d candidate headings extracted.",
            len(candidate_headings),
        )

        return candidate_headings

    @staticmethod
    def _clean_page_with_ollama(
        page_number: int,
        page_text: str,
        fallback_headings: list[str],
    ) -> list[str]:
        """
        Clean a single page's text using Ollama 1.7b.

        Args:
            page_number: Page number for logging.
            page_text: The OCR text from the page.
            fallback_headings: Heuristic headings to use on failure.

        Returns:
            List of cleaned headings for this page.
        """
        logger.debug("Cleaning text for page %d with Ollama...", page_number)
        try:
            prompt = PROMPT_TEMPLATE_CLEAN_PAGE.format(
                ocr_text=page_text,
            )

            response = OllamaClient.ask(OLLAMA_MODEL_CLEAN, prompt)
            parsed = OllamaClient.parse_json_array(response)

            if isinstance(parsed, list):
                page_headings = [
                    h.strip()
                    for h in parsed
                    if isinstance(h, str) and h.strip()
                ]
                return page_headings

        except Exception as e:
            logger.warning(
                "Page %d: Ollama cleaning failed: %s. Using heuristic headings.",
                page_number,
                e,
            )

        return fallback_headings
