import logging
from pathlib import Path
import shutil

logger = logging.getLogger("processing")


class CleanupService:
    """
    Cleans up temporary files and directories created during processing.
    """

    @staticmethod
    def cleanup(path: Path) -> None:
        """
        Remove a temporary file or directory.

        Args:
            path: Path to the temporary file or directory.
        """
        if not path.exists():
            return

        try:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink()
        except OSError:
            logger.exception(
                "Failed to clean up temporary path: %s",
                path,
            )