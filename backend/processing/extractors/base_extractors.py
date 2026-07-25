from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseExtractor(ABC):
    """
    Base class for all document extractors.
    """

    @abstractmethod
    def extract(self, file_path: Path) -> Any:
        """
        Extract structured data from the given document.

        Args:
            file_path: Absolute path to the document.

        Returns:
            Structured extracted data.
        """
        raise NotImplementedError