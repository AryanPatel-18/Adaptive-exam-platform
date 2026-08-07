import logging
from pathlib import Path
import re

import camelot
import pandas as pd

from processing.dtos import (
    ExtractedOption,
    ExtractedQuestion,
    ExtractionResult,
)
from processing.exceptions import ExtractionFailedException
from .base_extractors import BaseExtractor

logger = logging.getLogger("processing")


class QuestionBankExtractor(BaseExtractor):
    """
    Extracts structured questions from question bank PDFs.

    Uses Camelot lattice flavor for bordered tables, matching
    the logic from tests/Extraction Files Testing/questions_extraction.py.
    """

    # Column names matching the test file's expected structure
    EXPECTED_COLUMNS = [
        "sr_no",
        "unit",
        "question",
        "answer",
        "marks",
        "previous_year",
        "option1",
        "option2",
        "option3",
        "option4",
    ]

    # Main function that extracts data from the question bank
    def extract(self, file_path: Path) -> ExtractionResult:
        """
        Extract all questions from a question bank PDF.

        Args:
            file_path: Absolute path to the PDF.

        Returns:
            ExtractionResult containing all extracted questions.

        Raises:
            ExtractionFailedException:
                If the PDF cannot be processed or contains zero valid questions.
        """

        logger.info("Starting extraction for PDF file: %s", file_path)
        tables = self._read_pdf(file_path)
        logger.info("Camelot found %d tables in the PDF.", len(tables))

        result = ExtractionResult()
        seen_numbers = set()

        for i, table in enumerate(tables):
            logger.debug("Parsing table %d/%d...", i + 1, len(tables))

            try:
                questions = self._parse_table(table.df)
                for q in questions:
                    if q.number not in seen_numbers:
                        result.questions.append(q)
                        seen_numbers.add(q.number)
                    else:
                        logger.warning("Skipping duplicate question number %d", q.number)
            except Exception as exc:
                logger.error("Failed to parse table %d: %s", i + 1, exc, exc_info=True)

        if not result.questions:
            raise ExtractionFailedException("No valid questions found in the document.")

        # Filter out invalid questions (all-NaN options)
        original_count = len(result.questions)
        result.questions = [
            q for q in result.questions
            if not self._is_invalid_question(q)
        ]
        removed_count = original_count - len(result.questions)

        if removed_count > 0:
            logger.info(
                "Filtered out %d invalid questions (all-NaN options). Remaining: %d",
                removed_count,
                len(result.questions),
            )

        if not result.questions:
            raise ExtractionFailedException(
                "No valid questions found after filtering invalid entries."
            )

        logger.info(
            "Successfully extracted a total of %d questions from the PDF.",
            len(result.questions),
        )
        return result

    # Reading pdfs using Camelot
    def _read_pdf(self, file_path: Path):
        """
        Read the supplied PDF using Camelot with lattice flavor.

        We are using Camelot since that is specialized for this type of table and grid like structure extraction

        Args:
            file_path: Absolute path to the PDF.

        Returns:
            camelot.core.TableList containing all extracted tables.

        Raises:
            ExtractionFailedException:
                If the PDF cannot be read.
        """

        if not file_path.exists():
            raise ExtractionFailedException(
                f"Question bank does not exist: {file_path}"
            )

        try:
            logger.debug("Running Camelot lattice extraction on %s", file_path)
            return camelot.read_pdf(
                filepath=str(file_path),
                pages="all",
                flavor="lattice",
            )
        except Exception as exc:
            logger.error("Camelot failed to parse PDF '%s'", file_path.name, exc_info=True)
            raise ExtractionFailedException(
                f"Failed to read PDF '{file_path.name}'."
            ) from exc

    # Parses the dataframe into extracted questions
    def _parse_table(self, dataframe) -> list[ExtractedQuestion]:
        """
        Parse a Camelot dataframe into ExtractedQuestion DTOs.

        Args:
            dataframe: Camelot extracted dataframe.

        Returns:
            List of extracted questions.
        """

        # Remove completely empty rows
        dataframe = dataframe.replace("", pd.NA)
        dataframe = dataframe.dropna(how="all")
        dataframe = dataframe.reset_index(drop=True)

        # Ensure column count matches
        if len(dataframe.columns) != len(self.EXPECTED_COLUMNS):
            logger.warning(
                "Skipping table due to unexpected number of columns: %d (expected %d)",
                len(dataframe.columns),
                len(self.EXPECTED_COLUMNS),
            )
            return []

        dataframe.columns = self.EXPECTED_COLUMNS

        questions: list[ExtractedQuestion] = []

        for _, row in dataframe.iterrows():
            # Skip header rows accidentally extracted
            if str(row["sr_no"]).strip().lower() in ["sr. no.", "sr_no", "sr.no.", "sr no"]:
                continue

            question = self._parse_question(row)
            if question is not None:
                questions.append(question)

        return questions

    # Helper function to parse a question
    def _parse_question(self, row) -> ExtractedQuestion | None:
        """
        Parse a dataframe row into an ExtractedQuestion DTO. 

        Args:
            row: A single dataframe row representing one question.

        Returns:
            ExtractedQuestion, or None if the row is invalid.
        """

        question_number_str = self._clean_text(row["sr_no"])

        if not question_number_str.isdigit():
            return None

        question_number = int(question_number_str)
        question_text = self._clean_text(row["question"])

        # Skip invalid rows
        if not question_text or question_text.lower() == "nan":
            return None

        correct_answer = self._clean_text(row["answer"]).upper()

        if correct_answer not in {"A", "B", "C", "D"}:
            return None

        options = self._parse_options([
            row["option1"],
            row["option2"],
            row["option3"],
            row["option4"],
        ])

        if options is None:
            return None

        answer_index = ord(correct_answer) - ord("A")
        if 0 <= answer_index < len(options):
            options[answer_index].is_correct = True

        return ExtractedQuestion(
            number=question_number,
            text=question_text,
            options=options,
        )

    # Helper function to check if question is invalid
    def _is_invalid_question(self, question: ExtractedQuestion) -> bool:
        """
        Check if a question is invalid (all options are NaN/empty).

        Ported from tests/Extraction Files Testing/process_questions.py.

        Args:
            question: ExtractedQuestion to check.

        Returns:
            True if all options are NaN/empty.
        """

        if not question.options:
            return True

        return all(
            str(option.text).strip().lower() == "nan"
            for option in question.options
        )
    
    # Helper function to parse options
    def _parse_options(
        self,
        raw_options: list[str],
    ) -> list[ExtractedOption] | None:
        """
        Parse raw option strings into ExtractedOption DTOs.

        Args:
            raw_options: List of raw option strings.

        Returns:
            List of ExtractedOption objects, or None if invalid.
        """

        if len(raw_options) != 4:
            return None

        options: list[ExtractedOption] = []

        for option in raw_options:
            cleaned_option = self._clean_text(option)

            if not cleaned_option:
                return None

            options.append(
                ExtractedOption(
                    text=cleaned_option,
                )
            )

        if len(options) != 4:
            return None

        return options

    def _clean_text(self, text: str | None) -> str:
        """
        Normalize extracted text.

        Args:
            text: Raw text extracted from the PDF.

        Returns:
            A cleaned string with normalized whitespace.
        """

        if text is None:
            return ""

        text = str(text)
        text = text.replace("\n", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()