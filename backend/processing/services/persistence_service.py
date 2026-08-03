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
        Persist validated extraction results including questions,
        options, and topic assignments.

        Topics and subtopics from Ollama are stored as flattened
        Topic entries, each linked via QuestionTopic.

        Args:
            source_file: File that produced the extracted questions.
            extracted_questions: Validated extracted questions.

        Returns:
            List of persisted Question instances.
        """

        logger.info(
            "Persisting %d extracted questions for source_file_id=%s",
            len(extracted_questions),
            source_file.id,
        )

        # Create Question records
        questions = PersistenceService._create_questions(
            source_file=source_file,
            extracted_questions=extracted_questions,
        )
        logger.info("Successfully bulk created %d Question records.", len(questions))

        # Create QuestionOption records
        PersistenceService._create_question_options(
            questions=questions,
            extracted_questions=extracted_questions,
        )
        logger.info("Successfully bulk created QuestionOption records.")

        # Create Topic and QuestionTopic records
        topics = PersistenceService._get_or_create_topics_from_questions(
            workspace=source_file.workspace,
            extracted_questions=extracted_questions,
        )

        PersistenceService._create_question_topics(
            questions=questions,
            topics=topics,
            extracted_questions=extracted_questions,
        )
        logger.info("Successfully created QuestionTopic relationships.")

        # Create TopicFile relationships
        PersistenceService._create_topic_files(
            source_file=source_file,
            topics=topics,
        )
        logger.info("Successfully created TopicFile relationships.")

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
        logger.debug("Creating Question objects...")
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
        logger.debug("Creating QuestionOption objects...")
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
    def _get_or_create_topics_from_questions(
        workspace,
        extracted_questions: list[ExtractedQuestion],
    ) -> dict[str, Topic]:
        """
        Gather all unique topic names from extracted questions
        and get-or-create Topic records.

        Args:
            workspace: Workspace the topics belong to.
            extracted_questions: Questions with populated topics lists.

        Returns:
            Mapping of topic name to Topic instance.
        """
        logger.debug("Gathering unique topic names from extracted questions...")
        # Collect all unique topic names
        all_topic_names = set()
        for q in extracted_questions:
            for topic_name in q.topics:
                if topic_name and topic_name.strip():
                    all_topic_names.add(topic_name.strip())

        if not all_topic_names:
            return {}

        topic_list = sorted(list(all_topic_names))

        return PersistenceService._get_or_create_topics(
            workspace=workspace,
            topics=topic_list,
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
        logger.debug("Creating QuestionTopic relationships...")
        question_topics: list[QuestionTopic] = []

        for question, extracted_question in zip(
            questions,
            extracted_questions,
            strict=True,
        ):
            seen_topic_ids = set()
            for topic_name in extracted_question.topics:
                topic = topics.get(topic_name.strip())

                if topic is None or topic.id in seen_topic_ids:
                    continue

                seen_topic_ids.add(topic.id)
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
        logger.debug("Creating TopicFile relationships...")
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

    @staticmethod
    @transaction.atomic
    def save_topics(
        source_file: File,
        topics: list[str],
    ) -> dict[str, Topic]:
        """
        Persist validated topics extracted from a source file.

        Args:
            source_file: File from which the topics were extracted.
            topics: Validated topic names.

        Returns:
            Mapping of topic name to persisted Topic instance.
        """

        logger.info(
            "Persisting %d topics for source_file_id=%s",
            len(topics),
            source_file.id,
        )

        PersistenceService._validate_topics(
            topics=topics,
        )

        persisted_topics = PersistenceService._get_or_create_topics(
            workspace=source_file.workspace,
            topics=topics,
        )

        logger.info(
            "Successfully persisted %d topics.",
            len(persisted_topics),
        )

        PersistenceService._create_topic_files(
            source_file=source_file,
            topics=persisted_topics,
        )

        logger.info(
            "Successfully created TopicFile relationships."
        )

        return persisted_topics

    @staticmethod
    def _validate_topics(
        topics: list[str],
    ) -> None:
        """
        Validate the topic list before persistence.

        Args:
            topics: Validated topic names.

        Raises:
            ValueError: If the topic list is invalid.
        """
        logger.debug("Validating topics list...")
        if not topics:
            raise ValueError(
                "At least one topic is required."
            )

        if not all(isinstance(topic, str) for topic in topics):
            raise ValueError(
                "All topics must be strings."
            )

        if not all(topic.strip() for topic in topics):
            raise ValueError(
                "Topics cannot be empty."
            )

    @staticmethod
    def _get_existing_topics(
        workspace,
        topics: list[str],
    ) -> dict[str, Topic]:
        """
        Fetch existing Topic records indexed by name.

        Args:
            workspace: Workspace to scope the query to.
            topics: Validated topic names.

        Returns:
            Mapping of topic name to existing Topic instance.
        """
        logger.debug("Fetching existing Topic records for workspace...")
        existing_topics = Topic.objects.filter(
            workspace=workspace,
            name__in=topics,
        )

        return {
            topic.name: topic
            for topic in existing_topics
        }

    @staticmethod
    def _create_topics(
        workspace,
        topics: list[str],
    ) -> dict[str, Topic]:
        """
        Create Topic records that do not already exist.

        Args:
            workspace: Workspace the topics belong to.
            topics: Topic names that do not exist in the database.

        Returns:
            Mapping of topic name to created Topic instance.
        """
        logger.debug("Creating %d new Topic records...", len(topics))
        new_topics = [
            Topic(workspace=workspace, name=topic)
            for topic in topics
        ]

        created_topics = Topic.objects.bulk_create(
            new_topics,
            batch_size=500,
        )

        return {
            topic.name: topic
            for topic in created_topics
        }

    @staticmethod
    def _get_or_create_topics(
        workspace,
        topics: list[str],
    ) -> dict[str, Topic]:
        """
        Retrieve existing topics and create any missing ones.

        Args:
            workspace: Workspace to scope topics to.
            topics: Validated topic names.

        Returns:
            Mapping of topic name to persisted Topic instance.
        """
        logger.debug("Getting or creating Topic records...")
        existing_topics = PersistenceService._get_existing_topics(
            workspace=workspace,
            topics=topics,
        )

        missing_topics = [
            topic
            for topic in topics
            if topic not in existing_topics
        ]

        if not missing_topics:
            return existing_topics

        created_topics = PersistenceService._create_topics(
            workspace=workspace,
            topics=missing_topics,
        )

        existing_topics.update(created_topics)

        return existing_topics