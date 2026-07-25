import logging

from django.db import transaction

from files.models import File
from processing.dtos import ExtractedQuestion
from processing.models import (
    Question,
    QuestionOption,
    QuestionTopic,
    Topic,
    TopicFile,
)

logger = logging.getLogger("processing")


class PersistenceService:
    """
    Persists extracted processing data to the database.
    """

    @staticmethod
    @transaction.atomic
    def save(
        source_file: File,
        extracted_questions: list[ExtractedQuestion],
    ) -> list[Question]:
        """
        Persist validated extraction results.

        Args:
            source_file: File that produced the extracted questions.
            extracted_questions: Validated extracted questions.

        Returns:
            List of persisted Question instances.
        """

        logger.info("Persisting %d extracted questions for source_file_id=%s", len(extracted_questions), source_file.id)

        questions = PersistenceService._create_questions(
            source_file=source_file,
            extracted_questions=extracted_questions,
        )
        logger.info("Successfully bulk created %d Question records.", len(questions))

        PersistenceService._create_question_options(
            questions=questions,
            extracted_questions=extracted_questions,
        )
        logger.info("Successfully bulk created QuestionOption records.")

        return questions

    @staticmethod
    def _create_questions(
        source_file: File,
        extracted_questions: list[ExtractedQuestion],
    ) -> list[Question]:
        """
        Create and persist Question objects.

        Args:
            source_file: File from which the questions were extracted.
            extracted_questions: Validated extracted question DTOs.

        Returns:
            List of persisted Question instances.
        """

        questions = [
            Question(
                source_file=source_file,
                question_number=question.number,
                question_text=question.text,
            )
            for question in extracted_questions
        ]

        return Question.objects.bulk_create(
            questions,
            batch_size=500,
        )

    @staticmethod
    def _create_question_options(
        questions: list[Question],
        extracted_questions: list[ExtractedQuestion],
    ) -> None:
        """
        Create and persist QuestionOption objects.

        Args:
            questions: Persisted Question model instances.
            extracted_questions: Source ExtractedQuestion DTOs.
        """

        question_options: list[QuestionOption] = []

        for question, extracted_question in zip(
            questions,
            extracted_questions,
            strict=True,
        ):
            for option in extracted_question.options:
                question_options.append(
                    QuestionOption(
                        question=question,
                        text=option.text,
                        is_correct=option.is_correct,
                    )
                )

        QuestionOption.objects.bulk_create(
            question_options,
            batch_size=1000,
        )

    @staticmethod
    def _create_question_topics(
        questions: list[Question],
        topics: dict[str, Topic],
        extracted_questions: list[ExtractedQuestion],
    ) -> None:
        """
        Create QuestionTopic relationships.

        Args:
            questions: Persisted Question instances.
            topics: Mapping of topic name to Topic instance.
            extracted_questions: Source ExtractedQuestion DTOs.
        """

        question_topics: list[QuestionTopic] = []

        for question, extracted_question in zip(
            questions,
            extracted_questions,
            strict=True,
        ):
            for topic_name in extracted_question.topics:
                topic = topics.get(topic_name)

                if topic is None:
                    continue

                question_topics.append(
                    QuestionTopic(
                        question=question,
                        topic=topic,
                    )
                )

        QuestionTopic.objects.bulk_create(
            question_topics,
            batch_size=1000,
        )

    @staticmethod
    def _create_topic_files(
        source_file: File,
        topics: dict[str, Topic],
    ) -> None:
        """
        Create TopicFile relationships.

        Args:
            source_file: File from which the topics were extracted.
            topics: Mapping of topic name to Topic instance.
        """

        topic_files = [
            TopicFile(
                file=source_file,
                topic=topic,
            )
            for topic in topics.values()
        ]

        TopicFile.objects.bulk_create(
            topic_files,
            batch_size=500,
        )