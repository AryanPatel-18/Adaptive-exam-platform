# pyrefly: ignore [missing-import]
import joblib
import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


MODEL_PATH = (
    Path(__file__).resolve().parent
    / "ml"
    / "preparedness_model.pkl"
)

_model_config = None


def _load_model():
    global _model_config

    if _model_config is not None:
        return _model_config

    try:
        if not MODEL_PATH.exists():
            logger.error("Preparedness model file not found at %s", MODEL_PATH)
            raise FileNotFoundError(
                f"Preparedness model not found at {MODEL_PATH}"
            )

        logger.debug("Loading preparedness model from %s", MODEL_PATH)
        _model_config = joblib.load(MODEL_PATH)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load preparedness model from {MODEL_PATH}. "
            f"Ensure scikit-learn versions match between training and "
            f"inference environments. Original error: {exc}"
        ) from exc

    return _model_config


class PreparednessModel:
    """
    Handles all machine learning operations for preparedness prediction.
    """

    @staticmethod
    def engineer_features(
        *,
        total_topics,
        topics_attempted,
        total_questions,
        attempted_questions,
        correct_answers,
        wrong_answers,
        accuracy,
        coverage,
        average_time,
        improvement,
        consistency,
    ):
        attempt_rate = (
            attempted_questions / total_questions
            if total_questions > 0
            else 0
        )

        topic_attempt_rate = (
            topics_attempted / total_topics
            if total_topics > 0
            else 0
        )

        correct_ratio = (
            correct_answers / total_questions
            if total_questions > 0
            else 0
        )

        wrong_ratio = (
            wrong_answers / attempted_questions
            if attempted_questions > 0
            else 0
        )

        accuracy_coverage_interaction = (
            accuracy * coverage
        ) / 100

        time_efficiency = (
            accuracy / average_time
            if average_time > 0
            else 0
        )

        consistency_improvement_interaction = (
            consistency * improvement
        )

        return {
            "total_topics": total_topics,
            "topics_attempted": topics_attempted,
            "total_questions": total_questions,
            "attempted_questions": attempted_questions,
            "correct_answers": correct_answers,
            "wrong_answers": wrong_answers,
            "accuracy": accuracy,
            "coverage": coverage,
            "average_time": average_time,
            "improvement": improvement,
            "consistency": consistency,
            "attempt_rate": attempt_rate,
            "topic_attempt_rate": topic_attempt_rate,
            "correct_ratio": correct_ratio,
            "wrong_ratio": wrong_ratio,
            "accuracy_coverage_interaction": accuracy_coverage_interaction,
            "time_efficiency": time_efficiency,
            "consistency_improvement_interaction": consistency_improvement_interaction,
        }

    @staticmethod
    def predict(
        *,
        total_topics,
        topics_attempted,
        total_questions,
        attempted_questions,
        correct_answers,
        wrong_answers,
        accuracy,
        coverage,
        average_time,
        improvement,
        consistency,
    ):
        features = PreparednessModel.engineer_features(
            total_topics=total_topics,
            topics_attempted=topics_attempted,
            total_questions=total_questions, 
            attempted_questions=attempted_questions,
            correct_answers=correct_answers,
            wrong_answers=wrong_answers,
            accuracy=accuracy,
            coverage=coverage,
            average_time=average_time,
            improvement=improvement,
            consistency=consistency,
        )
        try:
            config = _load_model()

            dataframe = pd.DataFrame(
                [features],
                columns=config["feature_columns"],
            )

            preparedness_score = config["model"].predict(dataframe)[0]
        except (RuntimeError, ModuleNotFoundError) as exc:
            logger.error(
                "Model loading failed: %r. Falling back to heuristic preparedness calculation.",
                exc
            )
            # Fallback heuristic if the ML model fails to load (e.g., scikit-learn version mismatch)
            preparedness_score = min(
                100.0,
                (accuracy * 0.5) + (coverage * 0.3) + (consistency * 0.2)
            )

        logger.info("Final preparedness score: %s", preparedness_score)
        return round(float(preparedness_score), 2)
