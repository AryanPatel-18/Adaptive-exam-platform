import json
import logging
import requests
from schedule.exceptions import ScheduleGenerationFailedException

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen3:4b"
REQUEST_TIMEOUT = 300

class OllamaScheduleGenerator:
    """
    Responsible for generating study schedules
    using the locally hosted Ollama model.
    """

    @staticmethod
    def build_topic_prompt(topics_chunk):
        """
        Build the prompt sent to the Ollama model for a chunk of topics.
        """
        prompt = f"""
    You are an expert academic study planner.
    Evaluate the following topics based on their quiz performance and determine the study requirements.

    Topics:
    {json.dumps(topics_chunk, indent=4)}

    For each topic, provide:
    - The exact topic name as provided
    - Recommended study duration (in hours, e.g., 0.5, 1.0, 1.5). Allocate more time to lower accuracy topics.
    - Priority (High, Medium, Low)
    - A short 1-sentence reason why this topic needs study, referencing its accuracy.

    Return ONLY a JSON array. Do not return markdown. Do not wrap in code blocks.
    Format:
    [
        {{
            "topic": "Exact Topic Name",
            "duration_hours": 1.0,
            "priority": "High",
            "reason": "Needs immediate review due to 20% accuracy."
        }}
    ]
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
        Generate a study schedule using chunking for small LLMs.
        """
        logger.info("Starting schedule generation with model: %s", OLLAMA_MODEL)
        
        # Process all topics in a single chunk to prevent long sequential LLM delays,
        # but keep the simplified flat-array output format to ensure schema validity.
        chunk_size = max(len(topic_analysis), 1)
        all_topic_plans = []

        for i in range(0, len(topic_analysis), chunk_size):
            chunk = topic_analysis[i:i + chunk_size]
            logger.info("Processing chunk %d of %d (containing %d topics)", (i // chunk_size) + 1, (len(topic_analysis) + chunk_size - 1) // chunk_size, len(chunk))
            prompt = OllamaScheduleGenerator.build_topic_prompt(chunk)
            
            try:
                logger.debug("Sending HTTP POST to %s", OLLAMA_BASE_URL)
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
                logger.info("Received successful response from Ollama model.")
                
                logger.debug("Parsing JSON response...")
                plans = OllamaScheduleGenerator.parse_response(response.json())
                logger.info("Successfully extracted %d topic study plans from response.", len(plans) if isinstance(plans, list) else 1)
                
                if isinstance(plans, list):
                    all_topic_plans.extend(plans)
                elif isinstance(plans, dict) and "topics" in plans:
                    all_topic_plans.extend(plans["topics"])
                elif isinstance(plans, dict):
                    # fallback if it returned a single object instead of array
                    all_topic_plans.append(plans)

            except requests.RequestException as exc:
                logger.exception("Failed to communicate with Ollama service")
                raise ScheduleGenerationFailedException(
                    detail="Could not connect to the schedule generation service.",
                ) from exc

        # Assemble the schedule programmatically
        logger.info("Matching LLM plans with original topic analysis to ensure no topics were dropped...")
        returned_topics_map = {}
        for plan in all_topic_plans:
            t_name = str(plan.get("topic", "")).strip()
            if t_name:
                returned_topics_map[t_name.lower()] = plan

        final_topic_plans = []
        for topic_data in topic_analysis:
            t_name = topic_data.get("topic", "Unknown Topic")
            if t_name.lower() in returned_topics_map:
                final_topic_plans.append(returned_topics_map[t_name.lower()])
            else:
                # Fallback for topics dropped by the AI
                logger.warning("AI dropped topic '%s'. Generating programmatic fallback plan.", t_name)
                accuracy = float(topic_data.get("accuracy", 100))
                priority = "High" if accuracy < 40 else ("Medium" if accuracy < 70 else "Low")
                duration = 1.5 if priority == "High" else (1.0 if priority == "Medium" else 0.5)
                final_topic_plans.append({
                    "topic": t_name,
                    "duration_hours": duration,
                    "priority": priority,
                    "reason": f"Requires review based on {accuracy}% accuracy."
                })

        logger.info("Schedule assembly complete. Finalized %d topic plans.", len(final_topic_plans))

        overall_level = "Needs Improvement" if preparedness_score < 60 else ("Average" if preparedness_score < 80 else "Excellent")
        
        return {
            "summary": {
                "preparedness_score": round(preparedness_score, 2),
                "overall_level": overall_level,
                "recommendation": "Focus heavily on high priority topics early in your studies. Work through this list systematically."
            },
            "schedule": final_topic_plans
        }

    @staticmethod
    def parse_response(
        response,
    ):
        """
        Parse the generated JSON array returned by Ollama.
        """
        content = response.get("response", "").strip()

        start_idx = content.find('[')
        end_idx = content.rfind(']')
        
        # Try finding array first
        if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
            content = content[start_idx:end_idx+1]
        else:
            # Fallback to object
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
                content = content[start_idx:end_idx+1]

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            logger.error("Failed to decode JSON from Ollama. Raw content: %r", response.get("response", ""))
            return []