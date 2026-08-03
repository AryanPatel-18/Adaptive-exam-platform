import logging
from pathlib import Path
import tempfile

from files.models import File
from workspace.models import Workspace

from processing.extractors.notes_extraction import NotesExtractor
from processing.extractors.question_bank_extractor import QuestionBankExtractor

from processing.ocr.pdf_converter import PDFToImageConverter
from processing.ocr.image_preprocessor import ImagePreprocessor
from processing.ocr.easyocr_engine import EasyOCREngine

from processing.validators.question_validator import QuestionValidator
from processing.validators.text_normalizer import TopicExtractor
from processing.validators.topic_validator import TopicValidator

from processing.services.cleanup_service import CleanupService
from processing.services.download_service import DownloadService
from processing.services.persistence_service import PersistenceService

logger = logging.getLogger("processing")


class ProcessingService:
    """
    Orchestrates the complete document processing pipeline.
    """

    question_bank_extractor = QuestionBankExtractor()

    @staticmethod
    def process_notes(
        workspace: Workspace,
        source_file: File,
    ) -> None:
        """
        Process a single handwritten notes file.

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

        notes_extractor = NotesExtractor(
            pdf_converter=PDFToImageConverter(),
            image_preprocessor=ImagePreprocessor(),
            ocr_engine=EasyOCREngine(
                languages=["en"],
            ),
        )

        topic_extractor = TopicExtractor()

        topic_validator = TopicValidator()

        try:
            logger.info(
                "Step 1/5: Downloading notes file..."
            )

            local_file = DownloadService.download(
                file=source_file,
                destination=working_directory,
            )

            logger.info(
                "Successfully downloaded notes file to: %s",
                local_file,
            )

            logger.info(
                "Step 2/5: Extracting OCR text..."
            )

            ocr_result = notes_extractor.extract(
                pdf_path=local_file,
                output_directory=working_directory,
            )

            logger.info(
                "OCR extraction completed successfully."
            )

            logger.info(
                "Step 3/5: Extracting candidate topics..."
            )

            candidate_topics = topic_extractor.extract(
                text=ocr_result.text,
            )

            logger.info(
                "Extracted %d candidate topics.",
                len(candidate_topics),
            )

            logger.info(
                "Step 4/5: Validating topics..."
            )

            validated_topics = topic_validator.validate(
                topics=candidate_topics,
            )

            logger.info(
                "Validated %d topics.",
                len(validated_topics),
            )

            logger.info(
                "Step 5/5: Persisting topics..."
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
                ProcessingService.question_bank_extractor.extract(
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