import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, EndpointConnectionError
from decouple import config
import logging
from pathlib import Path

from storage.exceptions import (
    BucketCreationException,
    BucketNotFoundException,
    ObjectNotFoundException,
    PresignedURLException,
    StorageConnectionException,
    StorageException,
)

logger = logging.getLogger("files")

class MinIOProvider:
    """
    Low-level storage provider responsible for communicating directly with
    the S3-compatible object storage (MinIO).

    This class should be the only component that communicates directly
    with boto3. Higher layers (StorageService) should use this provider
    instead of interacting with boto3 themselves.
    """

    def __init__(self):
        self.endpoint = config("MINIO_ENDPOINT")
        self.access_key = config("MINIO_ACCESS_KEY")
        self.secret_key = config("MINIO_SECRET_KEY")
        self.bucket_name = config("MINIO_BUCKET")
        self.region = config("MINIO_REGION", default="us-east-1")

        self.use_ssl = (
            config("MINIO_SECURE", default="False")
            .strip()
            .lower()
            == "true"
        )

        self._client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            use_ssl=self.use_ssl,
            config=Config(signature_version="s3v4"),
        )

    def health_check(self) -> bool:
        """
        Verify that the storage service is reachable.

        Returns:
            bool: True if the connection succeeds.

        Raises:
            StorageConnectionException
        """
        try:
            self._client.list_buckets()
            return True

        except EndpointConnectionError as exc:
            logger.error("Storage connection failed: Unable to reach endpoint %s", self.endpoint)
            raise StorageConnectionException(
                detail="Unable to connect to the storage provider."
            ) from exc

        except ClientError as exc:
            logger.error("Storage connection failed: Unexpected client error %s", exc, exc_info=True)
            raise StorageConnectionException(
                detail="Storage provider returned an unexpected response."
            ) from exc

    def bucket_exists(self) -> bool:
        """
        Check whether the configured bucket exists.

        Returns:
            bool: True if the bucket exists, otherwise False.

        Raises:
            StorageConnectionException
        """
        try:
            self._client.head_bucket(Bucket=self.bucket_name)
            return True

        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]

            if error_code in ("404", "NoSuchBucket", "NotFound"):
                return False

            raise StorageConnectionException(
                detail="Unexpected error while checking bucket existence."
            ) from exc

    def create_bucket(self) -> None:
        """
        Create the configured bucket if it does not already exist.

        Raises:
            BucketCreationException
        """
        try:
            if self.bucket_exists():
                return

            logger.info("Creating missing bucket: %s", self.bucket_name)
            self._client.create_bucket(Bucket=self.bucket_name)

        except ClientError as exc:
            logger.error("Failed to create bucket %s: %s", self.bucket_name, exc, exc_info=True)
            raise BucketCreationException(
                detail=f"Unable to create bucket '{self.bucket_name}'."
            ) from exc

    def ensure_bucket_exists(self) -> None:
        """
        Ensure that the configured bucket exists.

        If the bucket does not exist, it will be created.

        Raises:
            BucketNotFoundException
        """
        if self.bucket_exists():
            return

        self.create_bucket()

        if not self.bucket_exists():
            raise BucketNotFoundException(
                detail=f"Bucket '{self.bucket_name}' does not exist."
            )
    
    def generate_upload_url(
        self,
        storage_key: str,
        content_type: str,
        expires_in: int = 900,
    ) -> str:
        """
        Generate a pre-signed URL for uploading an object directly to MinIO.

        The backend never receives the file contents. Instead, it generates
        a temporary URL which the frontend uses to upload the file directly
        to the object storage service.

        Args:
            storage_key:
                Destination object key inside the bucket.

            content_type:
                Expected MIME type of the uploaded object.

            expires_in:
                Number of seconds before the URL expires.

        Returns:
            A pre-signed PUT URL.
        """

        try:
            url = self._client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": storage_key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in,
            )
            logger.info("Generated pre-signed upload URL for storage key: %s (expires in %s seconds)", storage_key, expires_in)
            return url

        except ClientError as exc:
            logger.error("Failed to generate upload URL for storage key %s: %s", storage_key, exc, exc_info=True)
            raise PresignedURLException(
                detail="Failed to generate upload URL."
            ) from exc

    def get_object_metadata(
        self,
        storage_key: str,
    ) -> dict:
        """
        Retrieve metadata for an object stored in MinIO.

        This method is primarily used during upload verification to
        confirm that an uploaded object exists and matches the expected
        metadata.

        Args:
            storage_key:
                Object key inside the bucket.

        Returns:
            Dictionary containing the object's metadata.
        """

        try:
            response = self._client.head_object(
                Bucket=self.bucket_name,
                Key=storage_key,
            )

            return {
                "content_length": response["ContentLength"],
                "content_type": response["ContentType"],
                "etag": response["ETag"].strip('"'),
                "last_modified": response["LastModified"],
            }

        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")

            if error_code in ("404", "NoSuchKey", "NotFound"):
                logger.warning("Object metadata not found for key: %s", storage_key)
                raise ObjectNotFoundException(
                    detail="The requested object does not exist."
                ) from exc

            logger.error("Failed to retrieve object metadata for key %s: %s", storage_key, exc, exc_info=True)
            raise StorageException(
                detail="Failed to retrieve object metadata."
            ) from exc

    def get_object(
        self,
        storage_key: str,
    ):
        """
        Retrieve an object from the storage bucket as a streaming response.

        The caller is responsible for calling `.close()` and
        `.release_conn()` on the returned response body to avoid
        connection leaks.

        Args:
            storage_key:
                Object key inside the bucket.

        Returns:
            The raw streaming body of the S3 object response.

        Raises:
            ObjectNotFoundException
            StorageException
        """

        try:
            response = self._client.get_object(
                Bucket=self.bucket_name,
                Key=storage_key,
            )
            return response["Body"]

        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")

            if error_code in ("404", "NoSuchKey", "NotFound"):
                logger.warning("Object not found for key: %s", storage_key)
                raise ObjectNotFoundException(
                    detail="The requested object does not exist."
                ) from exc

            logger.error("Failed to retrieve object for key %s: %s", storage_key, exc, exc_info=True)
            raise StorageException(
                detail="Failed to retrieve object from storage."
            ) from exc

    def delete_object(
        self,
        storage_key: str,
    ) -> None:
        """
        Delete an object from the storage bucket.

        This method is used during upload session rollback to remove
        objects that were uploaded but ultimately failed verification.

        Args:
            storage_key:
                Object key inside the bucket.

        Raises:
            StorageException
        """

        try:
            self._client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_key,
            )
            logger.info("Successfully deleted object from storage: %s", storage_key)

        except ClientError as exc:
            logger.error("Failed to delete object %s from storage: %s", storage_key, exc, exc_info=True)
            raise StorageException(
                detail="Failed to delete object from storage."
            ) from exc

    def download_file(
        self,
        storage_key: str,
        destination: str | Path,
    ) -> Path:
        """
        Download a file from the storage bucket to a local path.

        Args:
            storage_key: Object key inside the bucket.
            destination: Local file path where the object should be downloaded.

        Returns:
            Absolute path to the downloaded file.

        Raises:
            StorageException:
                If the download fails.
        """

        destination = Path(destination)
        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            self._client.download_file(
                Bucket=self.bucket_name,
                Key=storage_key,
                Filename=str(destination),
            )

            logger.info(
                "Successfully downloaded object '%s' to '%s'.",
                storage_key,
                destination,
            )

            return destination

        except (ClientError, OSError) as exc:
            logger.error(
                "Failed to download object '%s': %s",
                storage_key,
                exc,
                exc_info=True,
            )

            raise StorageException(
                detail="Failed to download file from storage."
            ) from exc