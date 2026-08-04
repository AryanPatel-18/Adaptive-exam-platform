"""
Question topic extractor service.

Extracts topic and subtopic for each question using Ollama LLM,
then flattens both into the question's topics list.

Logic ported from tests/Extraction Files Testing/questions_extraction.py
and ollama_test.py.
"""

import logging

from processing.dtos import ExtractedQuestion
from processing.prompts import PROMPT_TEMPLATE_QUESTION_TOPICS
from processing.services.ollama_client import (
    OllamaClient,
    OLLAMA_MODEL_QUESTION_TOPICS,
)

logger = logging.getLogger("processing")

BATCH_SIZE = 5


class QuestionTopicExtractor:
    """
    Extracts topic and subtopic for each question using Ollama LLM
    batch processing.

    Both topic and subtopic are flattened into the question's
    topics list for storage as separate Topic entries.
    """

    @staticmethod
    def extract(
        questions: list[ExtractedQuestion],
    ) -> None:
        """
        Extract and assign topics to each question in-place.

        Sends questions in batches to Ollama for topic/subtopic
        classification. Both are flattened into the question's
        topics list.

        Falls back to assigning "Unknown" if Ollama is offline.

        Args:
            questions:
                List of ExtractedQuestion objects to annotate.
        """

        if not questions:
            return

        if not OllamaClient.check_status():
            logger.warning(
                "Ollama service is offline. Assigning 'Unknown' topics to all questions."
            )
            for q in questions:
                q.topics = ["Unknown"]
            return

        logger.info(
            "Extracting topics for %d questions using Ollama model '%s'...",
            len(questions),
            OLLAMA_MODEL_QUESTION_TOPICS,
        )

        OllamaClient.load_model(OLLAMA_MODEL_QUESTION_TOPICS)

        try:
            for start in range(0, len(questions), BATCH_SIZE):
                batch = questions[start : start + BATCH_SIZE]

                QuestionTopicExtractor._process_batch(
                    batch=batch,
                    batch_start=start,
                    total=len(questions),
                )

                logger.info(
                    "Processed topics: %d/%d",
                    min(start + BATCH_SIZE, len(questions)),
                    len(questions),
                )

        finally:
            OllamaClient.unload_model(OLLAMA_MODEL_QUESTION_TOPICS)

    @staticmethod
    def _process_batch(
        batch: list[ExtractedQuestion],
        batch_start: int,
        total: int,
    ) -> None:
        """
        Process a single batch of questions for topic extraction.

        Args:
            batch: List of questions in this batch.
            batch_start: Starting index of this batch.
            total: Total number of questions.
        """
        logger.debug("Processing topic extraction for batch starting at index %d...", batch_start)

        # Build the question block
        question_block = ""
        for idx, q in enumerate(batch):
            question_block += f"\nQuestion {idx + 1}:\n{q.text}\n"

        prompt = PROMPT_TEMPLATE_QUESTION_TOPICS.format(
            questions=question_block,
        )

        try:
            response = OllamaClient.ask(OLLAMA_MODEL_QUESTION_TOPICS, prompt)
            topic_results = OllamaClient.parse_json_array(response)

            if not isinstance(topic_results, list):
                raise ValueError("Response is not a JSON array")

            for idx, q in enumerate(batch):
                if idx < len(topic_results) and isinstance(topic_results[idx], dict):
                    topic = topic_results[idx].get("topic", "Unknown")
                    subtopic = topic_results[idx].get("subtopic", "Unknown")

                    # Flatten: both topic and subtopic become separate entries
                    topics = []
                    if topic and topic != "Unknown":
                        topics.append(topic.strip())
                    if subtopic and subtopic != "Unknown":
                        topics.append(subtopic.strip())

                    # Fallback if both were "Unknown"
                    if not topics:
                        topics = ["Unknown"]

                    q.topics = topics
                else:
                    q.topics = ["Unknown"]

        except Exception as e:
            logger.error(
                "Batch %d-%d failed: %s",
                batch_start,
                batch_start + len(batch),
                e,
            )
            for q in batch:
                q.topics = ["Unknown"]
