import logging
from pathlib import Path

from files.models import File
from storage.provider import MinIOProvider
from processing.exceptions import DownloadFailedException

logger = logging.getLogger("processing")


class DownloadService:
    """
    Downloads files required for processing.
    """

    provider = MinIOProvider()

    @staticmethod
    def download(
        file: File,
        destination: Path,
    ) -> Path:
        """
        Download a file to the specified destination.

        Args:
            file: File model instance.
            destination: Directory where the file should be downloaded.

        Returns:
            Absolute path to the downloaded file.

        Raises:
            DownloadFailedException:
                If the download fails.
        """

        destination.mkdir(
            parents=True,
            exist_ok=True,
        )

        local_file = destination / file.original_filename
        logger.debug("Starting download of file '%s' to local path: %s", file.original_filename, local_file)

        try:
            logger.info("Initiating download from MinIO for storage_key: %s", file.storage_key)
            DownloadService.provider.download_file(
                storage_key=file.storage_key,
                destination=local_file,
            )
            logger.info("Successfully downloaded '%s'.", file.original_filename)
        except Exception as exc:
            logger.error(
                "Failed to download '%s' from storage_key: %s", 
                file.original_filename, 
                file.storage_key, 
                exc_info=True
            )
            raise DownloadFailedException(
                f"Failed to download '{file.original_filename}'."
            ) from exc

        return local_file