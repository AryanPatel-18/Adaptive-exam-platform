"""
Topic validator.

Thin wrapper that coordinates the two-stage topic pipeline:
1. TopicCleaner — Ollama per-page heading cleaning
2. TopicFilter — Ollama cross-reference filtering against question bank topics

Replaces the previous generic LLM "validate topics" approach
that used the ollama Python library.
"""

import logging

from processing.dtos import NotesExtractionResult
from processing.services.topic_cleaner import TopicCleaner
from processing.services.topic_filter import TopicFilter

logger = logging.getLogger("processing")


class TopicValidator:
    """
    Validates and filters topics extracted from notes PDFs
    using a two-stage Ollama pipeline.

    Stage 1: Per-page heading cleaning (Ollama 1.7b)
    Stage 2: Cross-reference filtering against question bank topics (Ollama 4b)
    """

    @staticmethod
    def validate(
        extraction_result: NotesExtractionResult,
        workspace,
    ) -> list[str]:
        """
        Run the full two-stage topic validation pipeline.

        Args:
            extraction_result:
                NotesExtractionResult from the notes extractor.
            workspace:
                Workspace instance (used to query question bank topics from DB).

        Returns:
            A list of validated, filtered topic strings (max 40).
        """

        logger.info(
            "Stage 1: Running per-page heading cleaning..."
        )

        candidate_headings = TopicCleaner.clean(
            extraction_result=extraction_result,
        )

        logger.info(
            "Stage 1 complete. %d candidate headings.",
            len(candidate_headings),
        )

        logger.info(
            "Stage 2: Filtering candidates against question bank topics..."
        )

        filtered_topics = TopicFilter.filter(
            candidate_headings=candidate_headings,
            workspace=workspace,
        )

        logger.info(
            "Stage 2 complete. %d topics passed filtering.",
            len(filtered_topics),
        )

        return filtered_topics