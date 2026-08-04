import json

import requests

from schedule.exceptions import ScheduleGenerationFailedException


OLLAMA_BASE_URL = "http://localhost:11434/api/generate"

OLLAMA_MODEL = "qwen3:4b"

REQUEST_TIMEOUT = 300


class OllamaScheduleGenerator:
    """
    Responsible for generating study schedules
    using the locally hosted Ollama model.
    """

    @staticmethod
    def build_prompt(
        *,
        preparedness_score,
        topic_analysis,
        study_days,
        hours_per_day,
    ):
        """
        Build the prompt sent to the Ollama model.
        """

        prompt = f"""
    You are an expert academic study planner.

    Your task is to generate a personalized study schedule based on the student's quiz performance.

    Student Information
    -------------------
    Preparedness Score:
    {preparedness_score}/100

    Available Study Days:
    {study_days}

    Study Hours Per Day:
    {hours_per_day}

    Topic Analysis
    --------------
    {json.dumps(topic_analysis, indent=4)}

    Instructions
    ------------
    1. Carefully analyze the preparedness score.
    2. Prioritize weaker topics before stronger topics.
    3. Allocate more study time to topics with lower accuracy.
    4. Allocate less study time to topics with higher accuracy.
    5. Ensure the total study time for each day does not exceed the available hours.
    6. Include revision sessions throughout the schedule.
    7. Balance difficult and easy topics across different days.
    8. Distribute study time evenly across the available study days.
    9. Every study session must include a short explanation describing why that topic was scheduled.

    Return ONLY valid JSON.

    Return the schedule using the following format:

    {{
        "summary": {{
            "preparedness_score": 0,
            "overall_level": "",
            "recommendation": ""
        }},
        "schedule": [
            {{
                "day": 1,
                "topics": [
                    {{
                        "topic": "",
                        "duration_hours": 0,
                        "priority": "",
                        "reason": ""
                    }}
                ]
            }}
        ]
    }}

    Do not return markdown.
    Do not return explanations.
    Do not wrap the JSON inside code blocks.
    Return only the JSON object.
    """

        return prompt.strip()

    @staticmethod
    def generate_schedule(
        *,
        preparedness_score,
        topic_analysis,
        study_days,
        hours_per_day,
    ):
        """
        Generate a study schedule using the locally hosted
        Ollama model.
        """

        prompt = OllamaScheduleGenerator.build_prompt(
            preparedness_score=preparedness_score,
            topic_analysis=topic_analysis,
            study_days=study_days,
            hours_per_day=hours_per_day,
        )

        import logging
        logger = logging.getLogger(__name__)
        logger.info("Sending schedule generation prompt to Ollama model: %s", OLLAMA_MODEL)
        
        try:
            response = requests.post(
                OLLAMA_BASE_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()

        except requests.RequestException as exc:
            raise ScheduleGenerationFailedException(
                detail="Could not connect to the schedule generation service.",
            ) from exc

        return OllamaScheduleGenerator.parse_response(
            response.json(),
        )

    @staticmethod
    def parse_response(
        response,
    ):
        """
        Parse the generated schedule returned by Ollama.
        """

        import logging
        logger = logging.getLogger(__name__)

        content = response.get("response", "").strip()

        # Robust JSON extraction
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
            content = content[start_idx:end_idx+1]

        try:
            return json.loads(content)

        except json.JSONDecodeError as exc:
            logger.error("Failed to decode JSON from Ollama. Raw content: %r", response.get("response", ""))
            raise ScheduleGenerationFailedException(
                detail="The schedule generation service returned an invalid response.",
            ) from exc