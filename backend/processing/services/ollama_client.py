import json
import logging

import requests

logger = logging.getLogger("processing")

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

OLLAMA_MODEL_CLEAN = "qwen3:1.7b"
OLLAMA_MODEL_TOPICS = "qwen3:8b"
OLLAMA_MODEL_QUESTION_TOPICS = "qwen3:4b"


class OllamaClient:
    """
    HTTP client for interacting with the Ollama API.

    Uses raw requests.post() calls with explicit model lifecycle
    management (load/unload/keep_alive) rather than the ollama
    Python library.
    """

    @staticmethod
    def check_status() -> bool:
        """
        Check if the Ollama service is running and reachable.

        Returns:
            True if the Ollama API is responsive, False otherwise.
        """
        logger.debug("Checking Ollama service status at %s...", OLLAMA_TAGS_URL)
        try:
            response = requests.get(
                OLLAMA_TAGS_URL,
                timeout=2,
            )
            return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def load_model(model: str) -> None:
        """
        Warm up a model by sending a trivial prompt with keep_alive.

        Args:
            model: Name of the Ollama model to load.
        """

        logger.info("Loading Ollama model '%s'...", model)

        try:
            requests.post(
                OLLAMA_URL,
                json={
                    "model": model,
                    "prompt": "Model warmup",
                    "stream": False,
                    "keep_alive": "1h",
                },
                timeout=120,
            )
            logger.info("Ollama model '%s' loaded successfully.", model)
        except Exception as exc:
            logger.warning(
                "Failed to load Ollama model '%s': %s",
                model,
                exc,
            )

    @staticmethod
    def unload_model(model: str) -> None:
        """
        Force Ollama to unload a model from memory.

        Args:
            model: Name of the Ollama model to unload.
        """

        logger.info("Unloading Ollama model '%s'...", model)

        try:
            requests.post(
                OLLAMA_CHAT_URL,
                json={
                    "model": model,
                    "messages": [],
                    "keep_alive": 0,
                },
                timeout=10,
            )
            logger.info("Ollama model '%s' unloaded.", model)
        except Exception as exc:
            logger.warning(
                "Failed to unload Ollama model '%s': %s",
                model,
                exc,
            )

    @staticmethod
    def ask(model: str, prompt: str) -> str:
        """
        Send a prompt to an Ollama model and return the response text.

        Args:
            model: Name of the Ollama model.
            prompt: The prompt to send.

        Returns:
            The model's response text, or an empty string on failure.
        """

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "1h",
            },
            timeout=120,
        )

        if response.status_code == 200:
            return response.json().get("response", "")

        logger.error(
            "Ollama request failed with status %d: %s",
            response.status_code,
            response.text,
        )
        return ""

    @staticmethod
    def parse_json_array(text: str) -> list:
        """
        Robustly parse a JSON array from LLM output.

        Handles common LLM response patterns:
        - Wrapped in markdown code fences
        - Preceded/followed by explanation text
        - Direct JSON arrays

        Args:
            text: Raw LLM response text.

        Returns:
            Parsed JSON array.

        Raises:
            json.JSONDecodeError: If no valid JSON array can be found.
        """
        logger.debug("Parsing JSON array from LLM text response...")
        text = text.strip()

        # Strip markdown code fences
        if text.startswith("```"):
            lines = text.splitlines()
            if len(lines) >= 2:
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()

        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find array boundaries
        start_idx = text.find("[")
        end_idx = text.rfind("]")

        if start_idx != -1 and end_idx != -1:
            try:
                return json.loads(text[start_idx : end_idx + 1])
            except json.JSONDecodeError:
                pass

        raise json.JSONDecodeError(
            "No valid JSON array found in response",
            text,
            0,
        )
