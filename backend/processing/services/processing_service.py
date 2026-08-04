import logging
from pathlib import Path
import tempfile

from files.models import File
from workspace.models import Workspace
from common.choices import ProcessingStage
from processing.models import ProcessingJob

from processing.extractors.notes_extraction import NotesExtractor
from processing.extractors.question_bank_extractor import QuestionBankExtractor

from processing.validators.question_validator import QuestionValidator
from processing.validators.topic_validator import TopicValidator

from processing.services.cleanup_service import CleanupService
from processing.services.download_service import DownloadService
from processing.services.persistence_service import PersistenceService
from processing.services.question_topic_extractor import QuestionTopicExtractor

logger = logging.getLogger("processing")


class ProcessingService:
    """
    Orchestrates the complete document processing pipeline.

    Pipeline ordering: Question bank must be processed FIRST
    so that topics are available in the database for the notes
    pipeline to cross-reference.
    """

    question_bank_extractor = QuestionBankExtractor()

    @staticmethod
    def process(
        workspace: Workspace,
        source_file: File,
        job: ProcessingJob = None,
    ) -> None:
        """
        Process a single question bank file.

        Pipeline:
            1. Download file
            2. Extract questions (Camelot lattice + invalid-question filtering)
            3. Validate questions
            4. Extract topics via Ollama (batch topic/subtopic extraction)
            5. Persist questions, options, and flattened topic assignments

        Args:
            workspace: Workspace instance.
            source_file: File instance to process.
        """

        logger.info(
            "Starting question bank processing pipeline for workspace_id=%s, file_id=%s",
            workspace.id,
            source_file.id,
        )

        working_directory = Path(
            tempfile.mkdtemp(
                prefix=f"processing_{workspace.id}_",
            )
        )
        logger.debug("Created temporary working directory: %s", working_directory)

        try:
            # Step 1: Download
            if job:
                job.stage = ProcessingStage.DOWNLOADING
                job.save(update_fields=["stage"])
            logger.info("Step 1/5: Downloading source file...")
            local_file = DownloadService.download(
                file=source_file,
                destination=working_directory,
            )
            logger.info("Successfully downloaded source file to: %s", local_file)

            # Step 2: Extract questions
            if job:
                job.stage = ProcessingStage.EXTRACTING
                job.save(update_fields=["stage"])
            logger.info("Step 2/5: Extracting questions from file...")
            extraction_result = (
                ProcessingService.question_bank_extractor.extract(
                    local_file,
                )
            )
            logger.info(
                "Successfully extracted %d questions.",
                len(extraction_result.questions),
            )

            # Step 3: Validate
            if job:
                job.stage = ProcessingStage.VALIDATING
                job.save(update_fields=["stage"])
            logger.info("Step 3/5: Validating extracted questions...")
            QuestionValidator.validate(
                extraction_result.questions,
            )
            logger.info("Validation passed successfully.")

            # Step 4: Extract topics via Ollama
            logger.info("Step 4/5: Extracting topics for questions via Ollama...")
            QuestionTopicExtractor.extract(
                questions=extraction_result.questions,
            )
            logger.info("Topic extraction complete.")

            # Step 5: Persist
            if job:
                job.stage = ProcessingStage.PERSISTING
                job.save(update_fields=["stage"])
            logger.info("Step 5/5: Persisting questions, options, and topics to database...")
            PersistenceService.save(
                source_file=source_file,
                extracted_questions=extraction_result.questions,
            )
            logger.info("Successfully persisted all data to the database.")

            logger.info("Question bank processing pipeline completed successfully!")

        except Exception as exc:
            logger.error(
                "Processing pipeline failed for workspace_id=%s, file_id=%s. Error: %s",
                workspace.id,
                source_file.id,
                exc,
                exc_info=True,
            )
            raise

        finally:
            if job:
                job.stage = ProcessingStage.CLEANING_UP
                job.save(update_fields=["stage"])
            logger.debug("Cleaning up temporary directory: %s", working_directory)
            CleanupService.cleanup(
                working_directory,
            )
            logger.debug("Cleanup complete.")

    @staticmethod
    def process_notes(
        workspace: Workspace,
        source_file: File,
        job: ProcessingJob = None,
    ) -> None:
        """
        Process a single handwritten notes file.

        Pipeline:
            1. Download file
            2. Extract text with confidence tracking (direct text + OCR fallback)
            3. Ollama per-page heading cleaning
            4. Ollama cross-reference filtering against question bank topics from DB
            5. Persist filtered topics

        IMPORTANT: The question bank must be processed BEFORE this method
        is called, so that question topics exist in the database for
        cross-reference filtering.

        Args:
            workspace: Workspace instance.
            source_file: Notes file to process.
        """

        logger.info(
            "Starting notes processing pipeline for workspace_id=%s, file_id=%s",
            workspace.id,
            source_file.id,
        )

        working_directory = Path(
            tempfile.mkdtemp(
                prefix=f"processing_{workspace.id}_",
            )
        )

        logger.debug(
            "Created temporary working directory: %s",
            working_directory,
        )

        notes_extractor = NotesExtractor()

        try:
            # Step 1: Download
            if job:
                job.stage = ProcessingStage.DOWNLOADING
                job.save(update_fields=["stage"])
            logger.info(
                "Step 1/4: Downloading notes file..."
            )

            local_file = DownloadService.download(
                file=source_file,
                destination=working_directory,
            )

            logger.info(
                "Successfully downloaded notes file to: %s",
                local_file,
            )

            # Step 2: Extract text with confidence tracking
            if job:
                job.stage = ProcessingStage.EXTRACTING
                job.save(update_fields=["stage"])
            logger.info(
                "Step 2/4: Extracting text (direct + OCR fallback)..."
            )

            extraction_result = notes_extractor.extract(
                pdf_path=local_file,
                output_directory=working_directory,
            )

            logger.info(
                "Extraction completed: %d/%d pages processed.",
                extraction_result.pages_extracted,
                extraction_result.total_pages,
            )

            # Step 3 & 4: Two-stage topic validation
            if job:
                job.stage = ProcessingStage.VALIDATING
                job.save(update_fields=["stage"])
            logger.info(
                "Step 3/4: Running two-stage topic validation..."
            )

            validated_topics = TopicValidator.validate(
                extraction_result=extraction_result,
                workspace=workspace,
            )

            logger.info(
                "Validated %d topics.",
                len(validated_topics),
            )

            # Step 4: Persist
            if job:
                job.stage = ProcessingStage.PERSISTING
                job.save(update_fields=["stage"])
            logger.info(
                "Step 4/4: Persisting topics..."
            )

            PersistenceService.save_topics(
                source_file=source_file,
                topics=validated_topics,
            )

            logger.info(
                "Topics persisted successfully."
            )

            logger.info(
                "Notes processing pipeline completed successfully."
            )

        except Exception as exc:
            logger.error(
                "Notes processing pipeline failed for workspace_id=%s, file_id=%s. Error: %s",
                workspace.id,
                source_file.id,
                exc,
                exc_info=True,
            )
            raise

        finally:
            if job:
                job.stage = ProcessingStage.CLEANING_UP
                job.save(update_fields=["stage"])
            logger.debug(
                "Cleaning up temporary working directory: %s",
                working_directory,
            )

            CleanupService.cleanup(
                working_directory,
            )

            logger.debug(
                "Temporary working directory cleaned up successfully."
            )