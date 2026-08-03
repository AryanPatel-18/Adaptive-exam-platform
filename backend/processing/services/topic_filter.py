"""
Topic filter service.

Filters candidate headings from notes against question bank topics
using Ollama LLM cross-referencing with Python-based fallback.

Logic ported from tests/Extraction Files Testing/hand_notes_extraction.py
(filter_topics_by_questions_llm and filter_topics_by_questions functions).
"""

from __future__ import annotations

import difflib
import json
import logging
import re

from processing.extractors.notes_extraction import unique_preserve_order
from processing.models import Topic
from processing.prompts import PROMPT_TEMPLATE_FILTER_HEADINGS
from processing.services.ollama_client import (
    OllamaClient,
    OLLAMA_MODEL_TOPICS,
)

logger = logging.getLogger("processing")

STOP_WORDS = frozenset({
    "and", "the", "for", "with", "using", "from", "into", "this", "that", "these", "those",
    "under", "over", "each", "both", "all", "any", "some", "such", "other", "than", "then",
    "after", "before", "while", "during", "through", "between", "about", "against", "among",
    "out", "off", "again", "further", "once", "here", "there", "when",
    "where", "why", "how", "few", "more", "most",
})


class TopicFilter:
    """
    Filters candidate headings from notes against question bank
    topics to keep only relevant conceptual topics.

    Uses Ollama 4b for LLM-based filtering with Python-based
    keyword/fuzzy-matching fallback.
    """

    @staticmethod
    def filter(
        candidate_headings: list[str],
        workspace,
    ) -> list[str]:
        """
        Filter candidate headings against question bank topics.

        Attempts Ollama-based filtering first, falls back to
        pure Python filtering if Ollama is offline or fails.

        Args:
            candidate_headings:
                Candidate headings extracted from notes.
            workspace:
                Workspace instance to scope topic queries.

        Returns:
            Filtered list of up to 40 relevant topic strings.
        """

        if not candidate_headings:
            logger.info("No candidate headings to filter.")
            return []

        # Gather reference topics from the database
        reference_topics = TopicFilter._get_reference_topics(workspace)

        if not reference_topics:
            logger.warning(
                "No reference topics found in workspace. "
                "Returning candidate headings unfiltered (capped at 40)."
            )
            return candidate_headings[:40]

        # Try Ollama-based filtering first
        if OllamaClient.check_status():
            try:
                return TopicFilter._filter_with_ollama(
                    candidate_headings=candidate_headings,
                    reference_topics=reference_topics,
                )
            except Exception as e:
                logger.error(
                    "Ollama filtering failed: %s. Falling back to Python filtering.",
                    e,
                )

        else:
            logger.warning(
                "Ollama service offline. Using Python-based filtering."
            )

        # Python-based fallback
        return TopicFilter._filter_with_python(
            candidate_headings=candidate_headings,
            reference_topics=reference_topics,
        )

    @staticmethod
    def _get_reference_topics(workspace) -> set[str]:
        """
        Retrieve all unique topic names from the database for the
        given workspace.

        Args:
            workspace: Workspace to scope the query.

        Returns:
            Set of topic name strings (lowercased).
        """

        topics = Topic.objects.filter(
            workspace=workspace,
        ).values_list("name", flat=True)

        reference = set()
        for t in topics:
            if t:
                reference.add(t.strip().lower())

        logger.info(
            "Found %d reference topics in workspace.",
            len(reference),
        )

        return reference

    @staticmethod
    def _filter_with_ollama(
        candidate_headings: list[str],
        reference_topics: set[str],
    ) -> list[str]:
        """
        Filter candidates using Ollama 4b LLM.

        Args:
            candidate_headings: All candidate headings.
            reference_topics: Reference topic strings (lowercased).

        Returns:
            Filtered list of up to 40 relevant topics.
        """

        unique_candidates = sorted(list(set(candidate_headings)))
        reference_list = sorted(list(reference_topics))

        logger.info(
            "Filtering %d unique candidate headings using Ollama model '%s'...",
            len(unique_candidates),
            OLLAMA_MODEL_TOPICS,
        )

        OllamaClient.load_model(OLLAMA_MODEL_TOPICS)

        try:
            prompt = PROMPT_TEMPLATE_FILTER_HEADINGS.format(
                reference_topics=json.dumps(reference_list, indent=2),
                candidate_headings=json.dumps(unique_candidates, indent=2),
            )

            response = OllamaClient.ask(OLLAMA_MODEL_TOPICS, prompt)
            filtered_unique = OllamaClient.parse_json_array(response)

            if not isinstance(filtered_unique, list):
                raise ValueError("Ollama response is not a JSON list of strings")

            # Build approved set
            filtered_set = {
                h.strip().lower()
                for h in filtered_unique
                if isinstance(h, str)
            }

            def is_approved(heading: str) -> bool:
                h_clean = heading.strip().lower()
                if h_clean in filtered_set:
                    return True
                matches = difflib.get_close_matches(
                    h_clean,
                    list(filtered_set),
                    n=1,
                    cutoff=0.85,
                )
                return len(matches) > 0

            # Filter and preserve original order
            filtered = [h for h in candidate_headings if is_approved(h)]
            unique_filtered = unique_preserve_order(filtered)

            # Prioritize to max 40 if needed
            if len(unique_filtered) > 40:
                unique_filtered = TopicFilter._prioritize_top_40(
                    unique_filtered,
                    reference_topics,
                )

            final_filtered = unique_filtered[:40]

            logger.info(
                "Ollama filtering: Kept %d out of %d headings.",
                len(final_filtered),
                len(candidate_headings),
            )

            return final_filtered

        finally:
            OllamaClient.unload_model(OLLAMA_MODEL_TOPICS)

    @staticmethod
    def _filter_with_python(
        candidate_headings: list[str],
        reference_topics: set[str],
    ) -> list[str]:
        """
        Pure Python fallback topic filtering using keyword overlap
        and fuzzy matching.

        Args:
            candidate_headings: All candidate headings.
            reference_topics: Reference topic strings (lowercased).

        Returns:
            Filtered list of up to 40 relevant topics.
        """

        logger.info("Filtering candidate headings using Python-based approach...")

        # Extract keywords from reference topics
        question_keywords = set()
        for item in reference_topics:
            words = re.findall(r"[a-zA-Z0-9_]+", item)
            for w in words:
                w_lower = w.lower()
                if len(w_lower) > 2 and w_lower not in STOP_WORDS:
                    question_keywords.add(w_lower)

        def get_relevance_score(heading: str) -> tuple[int, int]:
            h_clean = heading.strip().lower()
            if not h_clean:
                return (0, 0)

            # Direct or fuzzy match
            matches = difflib.get_close_matches(
                h_clean,
                list(reference_topics),
                n=1,
                cutoff=0.8,
            )
            if h_clean in reference_topics or matches:
                return (2, len(h_clean))

            # Keyword overlap score
            heading_words = re.findall(r"[a-zA-Z0-9_]+", h_clean)
            score = sum(
                1 for w in heading_words
                if len(w) > 2 and w not in STOP_WORDS and w in question_keywords
            )
            if score > 0:
                return (1, score)

            return (0, 0)

        # Filter to keep only those with non-zero relevance
        related_candidates = [
            h for h in candidate_headings
            if get_relevance_score(h)[0] > 0
        ]

        unique_candidates = unique_preserve_order(related_candidates)

        # Score and sort
        scored = []
        for idx, h in enumerate(unique_candidates):
            score = get_relevance_score(h)
            scored.append((score, idx, h))

        scored.sort(key=lambda x: (x[0][0], x[0][1]), reverse=True)

        # Take top 40, re-sort into document order
        top_40 = {item[2] for item in scored[:40]}
        filtered_headings = [h for h in unique_candidates if h in top_40]

        logger.info(
            "Python filtering: kept %d out of %d headings.",
            len(filtered_headings),
            len(candidate_headings),
        )

        return filtered_headings

    @staticmethod
    def _prioritize_top_40(
        unique_filtered: list[str],
        reference_topics: set[str],
    ) -> list[str]:
        """
        When more than 40 approved headings exist, prioritize
        by relevance score.

        Args:
            unique_filtered: Approved unique headings.
            reference_topics: Reference topic strings (lowercased).

        Returns:
            Top 40 headings in original document order.
        """
        logger.debug("Prioritizing top 40 headings out of %d candidates...", len(unique_filtered))
        question_keywords = set()
        for item in reference_topics:
            words = re.findall(r"[a-zA-Z0-9_]+", item)
            for w in words:
                w_lower = w.lower()
                if len(w_lower) > 2 and w_lower not in STOP_WORDS:
                    question_keywords.add(w_lower)

        def get_relevance_score(heading: str) -> tuple[int, int]:
            h_clean = heading.strip().lower()
            if not h_clean:
                return (0, 0)
            matches = difflib.get_close_matches(
                h_clean,
                list(reference_topics),
                n=1,
                cutoff=0.8,
            )
            if h_clean in reference_topics or matches:
                return (2, len(h_clean))
            heading_words = re.findall(r"[a-zA-Z0-9_]+", h_clean)
            score = sum(
                1 for w in heading_words
                if len(w) > 2 and w not in STOP_WORDS and w in question_keywords
            )
            if score > 0:
                return (1, score)
            return (0, 0)

        scored = []
        for idx, h in enumerate(unique_filtered):
            score = get_relevance_score(h)
            scored.append((score, idx, h))

        scored.sort(key=lambda x: (x[0][0], x[0][1]), reverse=True)
        top_40 = {item[2] for item in scored[:40]}

        return [h for h in unique_filtered if h in top_40]
