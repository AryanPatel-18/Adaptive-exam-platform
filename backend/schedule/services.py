from django.db import transaction

from schedule.ml import PreparednessModel
from schedule.models import StudySchedule
from schedule.ollama import OllamaScheduleGenerator
from schedule.selectors import (
    AttemptAnalysisSelector,
)
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class PreparednessService:
    """
    Responsible for calculating the student's
    preparedness score using the trained ML model.
    """

    @staticmethod
    def calculate_preparedness(
        *,
        attempt,
    ):
        """
        Calculate the student's preparedness score using
        the trained ML model.
        """
        logger.debug("Calculating preparedness for attempt: %s", attempt.id)

        answers = AttemptAnalysisSelector.get_attempt_answers(
            attempt=attempt,
        )

        total_questions = attempt.quiz.total_questions

        attempted_questions = answers.count()

        correct_answers = answers.filter(
            is_correct=True,
        ).count()

        wrong_answers = answers.filter(
            is_correct=False,
        ).count()

        accuracy = (
            (correct_answers / attempted_questions) * 100
            if attempted_questions > 0
            else 0
        )

        workspace = attempt.quiz.workspace

        total_topics = AttemptAnalysisSelector.get_attempt_topics(
            workspace=workspace,
        ).count()

        topics_attempted = (
            answers.values(
                "question__question_topics__topic",
            )
            .distinct()
            .count()
        )

        coverage = (
            (topics_attempted / total_topics) * 100
            if total_topics > 0
            else 0
        )

        timed_answers = [
            (
                answer.answered_at -
                answer.loaded_at
            ).total_seconds()
            for answer in answers
            if answer.loaded_at and answer.answered_at
        ]

        average_time = (
            sum(timed_answers) / len(timed_answers)
            if timed_answers
            else 0
        )

        #
        # These will later be calculated from previous quiz attempts.
        #
        improvement = 50

        consistency = 50

        preparedness_score = PreparednessModel.predict(
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

        logger.info("Calculated preparedness score: %s for attempt: %s", preparedness_score, attempt.id)
        return preparedness_score


class TopicAnalysisService:

    @staticmethod
    def analyze_topics(
        *,
        attempt,
    ):
        """
        Analyze the student's topic-wise performance.
        """
        logger.debug("Analyzing topics for attempt: %s", attempt.id)

        topics = AttemptAnalysisSelector.get_attempt_topics(
            workspace=attempt.quiz.workspace,
        )

        analysis = []

        for topic in topics:

            answers = (
                AttemptAnalysisSelector.get_topic_answers(
                    attempt=attempt,
                    topic=topic,
                )
            )

            total_questions = answers.count()

            if total_questions == 0:
                continue

            correct_answers = answers.filter(
                is_correct=True,
            ).count()

            wrong_answers = answers.filter(
                is_correct=False,
            ).count()

            accuracy = (
                (correct_answers / total_questions) * 100
            )

            priority_score = (
                100 - accuracy
            )

            analysis.append(
                {
                    "topic": topic.name,
                    "correct_answers": correct_answers,
                    "wrong_answers": wrong_answers,
                    "accuracy": round(
                        accuracy,
                        2,
                    ),
                    "priority_score": round(
                        priority_score,
                        2,
                    ),
                }
            )

        analysis.sort(
            key=lambda topic: topic["priority_score"],
            reverse=True,
        )

        logger.info("Completed topic analysis for attempt: %s. Found %d active topics.", attempt.id, len(analysis))
        return analysis


class ScheduleGenerationService:
    """
    Responsible for the complete schedule
    generation workflow.
    """

    @staticmethod
    def generate_schedule(
        *,
        attempt_id,
        user,
        study_days,
        hours_per_day,
        start_date,
    ):
        """
        Generate a personalized study schedule for a quiz attempt.
        """
        logger.info("Starting schedule generation workflow for attempt_id: %s", attempt_id)

        attempt = AttemptAnalysisSelector.get_attempt(
            attempt_id=attempt_id,
            user=user,
        )

        preparedness_score = (
            PreparednessService.calculate_preparedness(
                attempt=attempt,
            )
        )

        topic_analysis = (
            TopicAnalysisService.analyze_topics(
                attempt=attempt,
            )
        )

        generated_plan = (
            OllamaScheduleGenerator.generate_schedule(
                preparedness_score=preparedness_score,
                topic_analysis=topic_analysis,
                study_days=study_days,
                hours_per_day=hours_per_day,
            )
        )

        logger.info("LLM generation completed. Saving schedule to database.")

        end_date = (
            start_date +
            timedelta(days=study_days - 1)
        )

        with transaction.atomic():
            StudySchedule.objects.filter(
                workspace=attempt.quiz.workspace,
                is_active=True,
            ).update(
                is_active=False,
            )

            schedule = StudySchedule.objects.create(
                user=user,
                workspace=attempt.quiz.workspace,
                quiz_attempt=attempt,
                preparedness_score=preparedness_score,
                generated_plan=generated_plan,
                hours_per_day=hours_per_day,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
            )

        logger.info("Schedule %s generated and saved successfully.", schedule.id)
        return schedule