import logging
import json

logger = logging.getLogger("processing")
import re
from ollama import chat, Client, ResponseError
from processing.exceptions import TopicValidationException

class TopicValidator:
    """
    Validates candidate topics using a local Ollama model.
    """

    def __init__(
        self,
        model: str = "qwen3:1.7b",
    ) -> None:
        """
        Initialize the topic validator.

        Args:
            model:
                Name of the Ollama model to use.
        """

        self._model = model
        self._client = Client()

        try:
            logger.debug("Checking for Ollama model '%s'...", self._model)
            available_models = self._client.list()

            if not any(
                model_info.model == self._model
                for model_info in available_models.models
            ):
                logger.error("Ollama model '%s' is not installed.", self._model)
                raise ValueError(
                    f"Ollama model '{self._model}' is not installed."
                )

        except ResponseError as exc:
            logger.error("Failed to connect to Ollama server: %s", exc)
            raise RuntimeError(
                "Unable to connect to the Ollama server."
            ) from exc

    def validate(
        self,
        topics: list[str],
    ) -> list[str]:
        """
        Validate candidate topics using the LLM.

        Args:
            topics:
                Candidate topics extracted from OCR text.

        Returns:
            A list of validated topics.
        """

        logger.info("Starting Ollama validation for %d candidate topics...", len(topics))
        prompt = self._build_prompt(
            topics=topics,
        )

        logger.debug("Querying Ollama model '%s'...", self._model)
        response = self._query_model(
            prompt=prompt,
        )

        validated_topics = self._parse_response(
            response=response,
        )

        normalized_topics = [
            self._normalize_topic(topic=topic)
            for topic in validated_topics
        ]

        unique_topics = self._remove_duplicates(
            topics=normalized_topics,
        )

        logger.info("Ollama validation complete. Returning %d validated topics.", len(unique_topics))
        return unique_topics

    def _build_prompt(
        self,
        topics: list[str],
    ) -> str:
        """
        Build the prompt sent to the LLM.
        """

        prompt = f"""
            You are an academic topic validator.

            Your task is to clean and normalize a list of candidate topics extracted using OCR.

            Rules:

            1. Remove OCR mistakes and meaningless text.
            2. Remove page numbers, symbols, random words and numbers.
            3. Merge duplicate topics.
            4. Correct obvious spelling mistakes.
            5. Expand abbreviations only when you are highly confident.
            6. Preserve valid academic topics exactly.
            7. Do not invent new topics.

            Return ONLY a JSON array of strings.

            Candidate Topics:
            {json.dumps(topics, indent=4)}
        """

        return prompt.strip()

    def _query_model(
        self,
        prompt: str,
    ) -> str:
        """
        Send the prompt to Ollama and return the raw response.
        """

        response = chat(
            model=self._model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            format={
                "type": "object",
                "properties": {
                    "topics": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                    },
                },
                "required": [
                    "topics",
                ],
            },
            options={
                "temperature": 0,
            },
        )

        return response.message.content

    def _parse_response(
        self,
        response: str,
    ) -> list[str]:
        """
        Parse the model response into a list of validated topics.
        """

        try:
            data = json.loads(response)

        except json.JSONDecodeError as exc:
            logger.error("Failed to parse JSON from Ollama response: %s", response)
            raise TopicValidationException(
                "Failed to parse Ollama response."
            ) from exc

        topics = data.get("topics")

        if topics is None:
            logger.error("Missing 'topics' field in Ollama response.")
            raise TopicValidationException(
                "Missing 'topics' field in Ollama response."
            )

        if not isinstance(
            topics,
            list,
        ):
            logger.error("'topics' field in Ollama response is not a list.")
            raise TopicValidationException(
                "'topics' must be a list."
            )

        if not all(
            isinstance(
                topic,
                str,
            )
            for topic in topics
        ):
            logger.error("Ollama response contains non-string topics.")
            raise TopicValidationException(
                "All topics must be strings."
            )

        return topics

    def _normalize_topic(
        self,
        topic: str,
    ) -> str:
        """
        Normalize a validated topic before persistence.
        """

        topic = topic.strip()

        topic = re.sub(
            r"\s+",
            " ",
            topic,
        )

        topic = topic.strip(
            ".,:;!?-_()[]{}<>\"'"
        )

        topic = topic.title()

        # Enforce DB length limit (models.Topic.name is max_length=255)
        if len(topic) > 255:
            logger.warning("Truncating excessively long topic: %s", topic)
            topic = topic[:255]

        return topic

    def _remove_duplicates(
        self,
        topics: list[str],
    ) -> list[str]:
        """
        Remove duplicate topics while preserving their original order.
        """

        unique_topics: list[str] = []
        seen: set[str] = set()

        for topic in topics:
            if topic in seen:
                continue

            seen.add(topic)
            unique_topics.append(topic)

        return unique_topics