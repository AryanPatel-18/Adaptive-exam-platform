import logging
from pathlib import Path
import re

import camelot

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
    """

    QUESTION_NUMBER_COLUMN = "Sr. No."
    QUESTION_TEXT_COLUMN = "Question_text"
    ANSWER_COLUMN = "answer"
    OPTION_COLUMNS = (
        "option1 (A)",
        "option2 (B)",
        "option3 (C)",
        "option4 (D)",
    )

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
            logger.info("Table %d shape: %s", i + 1, table.df.shape)
            logger.info("Raw dataframe top rows:\n%s", table.df.head(5).to_string())
            
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

        logger.info("Successfully extracted a total of %d questions from the PDF.", len(result.questions))
        return result

    def _read_pdf(self, file_path: Path):
        """
        Read the supplied PDF using Camelot.

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
            logger.debug("Running Camelot stream extraction on %s", file_path)
            return camelot.read_pdf(
                filepath=str(file_path),
                pages="all",
                flavor="stream",
            )
        except Exception as exc:
            logger.error("Camelot failed to parse PDF '%s'", file_path.name, exc_info=True)
            raise ExtractionFailedException(
                f"Failed to read PDF '{file_path.name}'."
            ) from exc

    def _parse_table(self, dataframe) -> list[ExtractedQuestion]:
        """
        Parse a Camelot dataframe into ExtractedQuestion DTOs.

        Args:
            dataframe: Camelot extracted dataframe.

        Returns:
            List of extracted questions.
        """

        if dataframe.shape[1] != 10:
            logger.warning("Skipping table due to unexpected number of columns: %d", dataframe.shape[1])
            return []

        # Dynamically locate the header row
        header_idx = -1
        for idx, row in dataframe.head(10).iterrows():
            col0 = self._clean_text(row.iloc[0]).lower()
            col2 = self._clean_text(row.iloc[2]).lower()
            if "sr." in col0 or "question_text" in col2:
                header_idx = idx
                break

        if header_idx != -1:
            dataframe = dataframe.iloc[header_idx + 1:].reset_index(drop=True)
            logger.debug("Discarded %d header rows.", header_idx + 1)
        else:
            logger.debug("No textual header found; assuming continuation table.")

        # Map by reliable column position
        dataframe.columns = [
            self.QUESTION_NUMBER_COLUMN,
            "unit_number",
            self.QUESTION_TEXT_COLUMN,
            self.ANSWER_COLUMN,
            "Marks",
            "Previous Year",
            self.OPTION_COLUMNS[0],
            self.OPTION_COLUMNS[1],
            self.OPTION_COLUMNS[2],
            self.OPTION_COLUMNS[3],
        ]

        questions: list[ExtractedQuestion] = []

        for _, row in dataframe.iterrows():
            question_number = self._clean_text(
                row[self.QUESTION_NUMBER_COLUMN]
            )

            if not question_number.isdigit():
                continue

            if not self._is_valid_mcq(row):
                continue

            parsed = self._parse_question(row)

            if parsed is not None:
                questions.append(parsed)

        return questions

    def _parse_question(self, row) -> ExtractedQuestion:
        """
        Parse a dataframe row into an ExtractedQuestion DTO.

        Args:
            row: A single dataframe row representing one question.

        Returns:
            ExtractedQuestion.
        """

        question_number = int(
            self._clean_text(
                row[self.QUESTION_NUMBER_COLUMN]
            )
        )

        question_text = self._clean_text(
            row[self.QUESTION_TEXT_COLUMN]
        )

        correct_answer = self._clean_text(
            row[self.ANSWER_COLUMN]
        ).upper()

        options = self._parse_options(
            [
                row[column]
                for column in self.OPTION_COLUMNS
            ]
        )

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

    def _is_valid_mcq(self, row) -> bool:
        """
        Determine whether a row represents a valid MCQ.

        A row is a valid MCQ if:
            - The answer column contains exactly one letter from {A, B, C, D}.
            - All four option columns contain non-empty text (which may be numeric).
            - The question text is not empty.

        Args:
            row: A single dataframe row.

        Returns:
            True if the row is a valid MCQ, False otherwise.
        """

        answer = self._clean_text(row[self.ANSWER_COLUMN]).upper()
        VALID_ANSWERS = frozenset({"A", "B", "C", "D"})
        if answer not in VALID_ANSWERS:
            return False
            
        question_text = self._clean_text(row.get(self.QUESTION_TEXT_COLUMN, ""))
        if not question_text:
            return False

        for column in self.OPTION_COLUMNS:
            option_text = self._clean_text(row[column])

            if not option_text:
                return False

        return True

    def _parse_options(
        self,
        raw_options: list[str],
    ) -> list[ExtractedOption] | None:
        """
        Parse raw option strings into ExtractedOption DTOs.

        Args:
            raw_options: List of raw option strings.

        Returns:
            List of ExtractedOption objects, or None if the
            question does not have exactly four valid options.
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
            A cleaned string with normalized whitespace, preserving newlines.
        """

        if text is None:
            return ""

        text = str(text)

        # Normalize carriage returns to newlines but preserve the newlines
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")
        
        # Replace multiple spaces with a single space
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()