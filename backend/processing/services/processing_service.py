import logging
from pathlib import Path
import tempfile

from files.models import File
from workspace.models import Workspace

from processing.services.cleanup_service import CleanupService
from processing.services.download_service import DownloadService
from processing.services.persistence_service import PersistenceService
from processing.extractors.question_bank_extractor import QuestionBankExtractor
from processing.validators.question_validator import QuestionValidator


logger = logging.getLogger("processing")


class ProcessingService:
    """
    Orchestrates the complete document processing pipeline.
    """

    extractor = QuestionBankExtractor()

    @staticmethod
    def process(
        workspace: Workspace,
        source_file: File,
    ) -> None:
        """
        Process a single question bank file.

        Args:
            workspace: Workspace instance.
            source_file: File instance to process.
        """
        logger.info(
            "Starting processing pipeline for workspace_id=%s, file_id=%s",
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
            logger.info("Step 1/4: Downloading source file...")
            local_file = DownloadService.download(
                file=source_file,
                destination=working_directory,
            )
            logger.info("Successfully downloaded source file to: %s", local_file)

            logger.info("Step 2/4: Extracting questions from file...")
            extraction_result = (
                ProcessingService.extractor.extract(
                    local_file,
                )
            )
            logger.info(
                "Successfully extracted %d questions.", 
                len(extraction_result.questions)
            )

            logger.info("Step 3/4: Validating extracted questions...")
            QuestionValidator.validate(
                extraction_result.questions,
            )
            logger.info("Validation passed successfully.")

            logger.info("Step 4/4: Persisting questions to database...")
            PersistenceService.save(
                source_file=source_file,
                extracted_questions=extraction_result.questions,
            )
            logger.info("Successfully persisted questions to the database.")

            logger.info("Processing pipeline completed successfully!")

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
            logger.debug("Cleaning up temporary directory: %s", working_directory)
            CleanupService.cleanup(
                working_directory,
            )
            logger.debug("Cleanup complete.")