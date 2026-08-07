from django.conf import settings
from django.db import models
from common.choices import UploadSessionStatus, FileRole, UploadFileStatus, FileStatus
from common.models import BaseModel
from workspace.models import Workspace


class UploadSession(BaseModel):
    """
    Represents a single upload transaction for a workspace.

    An upload session tracks the lifecycle of one upload operation,
    including all files expected to be uploaded as part of that
    transaction. It is also responsible for handling the verification of the uploaded files
    """

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="upload_sessions",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="upload_sessions",
    )

    status = models.CharField(
        max_length=32,
        choices=UploadSessionStatus.choices,
        default=UploadSessionStatus.PENDING,
    )

    expected_file_count = models.PositiveIntegerField()

    uploaded_file_count = models.PositiveIntegerField(
        default=0,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    
    cleanup_completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    
    expected_total_size = models.BigIntegerField(
        default=0,
    )

    expires_at = models.DateTimeField()

    class Meta:
        db_table = "upload_sessions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workspace"]),
            models.Index(fields=["user"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return (
            f"UploadSession("
            f"id={self.id}, "
            f"workspace={self.workspace_id}, "
            f"status={self.status}"
            f")"
        )

class UploadSessionFile(BaseModel):

    """
    Represents a single file expected to be uploaded as part of an
    UploadSession.

    These records are temporary and exist only to track and verify
    uploads before they become permanent workspace files.

    This is basically a temporary record for storing file information that is 
    currently present in the session and are processing
    """

    upload_session = models.ForeignKey(
        UploadSession,
        on_delete=models.CASCADE,
        related_name="files",
    )

    original_filename = models.CharField(
        max_length=255,
    )

    storage_key = models.CharField(
        max_length=1024,
        unique=True,
    )

    role = models.CharField(
        max_length=32,
        choices=FileRole.choices,
    )

    status = models.CharField(
        max_length=32,
        choices=UploadFileStatus.choices,
        default=UploadFileStatus.PENDING,
    )

    expected_file_size = models.BigIntegerField()

    expected_content_type = models.CharField(
        max_length=100,
    )

    uploaded_file_size = models.BigIntegerField(
        null=True,
        blank=True,
    )

    uploaded_content_type = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    # Unique Identification token generated based on the file hash
    etag = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    failure_reason = models.TextField(
        null=True,
        blank=True,
    )

    object_last_modified = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "upload_session_files"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["upload_session"]),
            models.Index(fields=["status"]),
            models.Index(fields=["role"]),
            models.Index(fields=["storage_key"]),
        ]

    def __str__(self):
        return (
            f"UploadSessionFile("
            f"filename={self.original_filename}, "
            f"status={self.status}"
            f")"
        )

class File(BaseModel):
    """
    Represents a permanent file belonging to a workspace.

    A File record is created only after an UploadSession has been
    successfully completed and every uploaded object has passed
    verification.

    This model is the source of truth for every file associated
    with a workspace. Or in simpler terms its the record of the permanent
    files that are stored in the bucket
    """

    workspace = models.ForeignKey(
        "workspace.Workspace",
        on_delete=models.CASCADE,
        related_name="files",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_files",
    )

    upload_session = models.ForeignKey(
        UploadSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_files",
    )

    original_filename = models.CharField(
        max_length=255,
    )

    # The path of the file inside the MiniIO Provider
    storage_key = models.CharField(
        max_length=1024,
        unique=True,
    )

    role = models.CharField(
        max_length=32,
        choices=FileRole.choices,
    )

    mime_type = models.CharField(
        max_length=100,
    )

    file_size = models.BigIntegerField()

    file_hash = models.CharField(
        max_length=64,
    )

    status = models.CharField(
        max_length=32,
        choices=FileStatus.choices,
        default=FileStatus.ACTIVE,
    )

    last_processed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "files"
        ordering = ["created_at"]

        indexes = [
            models.Index(fields=["workspace"]),
            models.Index(fields=["role"]),
            models.Index(fields=["status"]),
            models.Index(fields=["file_hash"]),
            models.Index(fields=["uploaded_by"]),
        ]

    def __str__(self):
        return (
            f"File("
            f"filename={self.original_filename}, "
            f"workspace={self.workspace_id}"
            f")"
        )