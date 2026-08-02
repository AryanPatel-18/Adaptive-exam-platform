import re


class TopicExtractor:
    """
    Extracts candidate topics from OCR text.
    """

    def extract(
        self,
        text: str,
    ) -> list[str]:
        """
        Extract candidate topics from OCR text.

        Args:
            text:
                Raw text extracted by the OCR engine.

        Returns:
            A list of candidate topics.
        """

        normalized_text = self._normalize_text(
            text=text,
        )

        lines = self._split_lines(
            text=normalized_text,
        )

        candidates: list[str] = []

        for line in lines:
            cleaned_line = self._clean_line(
                line=line,
            )

            if not self._is_valid_candidate(
                line=cleaned_line,
            ):
                continue

            candidates.append(
                cleaned_line,
            )

        return self._remove_duplicates(
            topics=candidates,
        )

    def _normalize_text(
        self,
        text: str,
    ) -> str:
        """
        Normalize OCR text.
        """

        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()

    def _split_lines(
        self,
        text: str,
    ) -> list[str]:
        """
        Split text into non-empty lines.
        """

        return [
            line.strip()
            for line in text.split("\n")
            if line.strip()
        ]

    def _clean_line(
        self,
        line: str,
    ) -> str:
        """
        Remove common OCR artifacts from a line.
        """

        line = re.sub(
            r"^\d+[\.\):-]?\s*",
            "",
            line,
        )

        line = re.sub(
            r"^[•\-\*]+\s*",
            "",
            line,
        )

        line = re.sub(
            r"\s+",
            " ",
            line,
        )

        return line.strip(" .,:;()[]{}")

    def _is_valid_candidate(
        self,
        line: str,
    ) -> bool:
        """
        Determine whether a cleaned line is a valid topic candidate.
        """

        if not line:
            return False

        if len(line) < 3:
            return False

        if line.isnumeric():
            return False

        if re.fullmatch(
            r"[\W_]+",
            line,
        ):
            return False

        if re.fullmatch(
            r"Page\s+\d+",
            line,
            flags=re.IGNORECASE,
        ):
            return False

        return True

    def _remove_duplicates(
        self,
        topics: list[str],
    ) -> list[str]:
        """
        Remove duplicate topics while preserving order.
        """

        seen: set[str] = set()
        unique_topics: list[str] = []

        for topic in topics:
            key = topic.casefold()

            if key in seen:
                continue

            seen.add(
                key,
            )

            unique_topics.append(
                topic,
            )

        return unique_topics