from django.db import models

class AccountStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    SUSPENDED = "SUSPENDED", "Suspended"


class TransactionReason(models.TextChoices):
    INITIAL_ALLOCATION = "INITIAL_ALLOCATION", "Initial Allocation"
    QUIZ_GENERATION = "QUIZ_GENERATION", "Quiz Generation"
    QUIZ_EVALUATION = "QUIZ_EVALUATION", "Quiz Evaluation"
    OCR_PROCESSING = "OCR_PROCESSING", "OCR Processing"
    FILE_PROCESSING = "FILE_PROCESSING", "File Processing"
    MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT", "Manual Adjustment"
    REFUND = "REFUND", "Refund"

class TransactionType(models.TextChoices):
    CREDIT = "CREDIT", "Credit"
    DEBIT = "DEBIT", "Debit"

class WorkspaceStatus(models.TextChoices):
    EMPTY = "EMPTY", "Empty"
    READY_FOR_PROCESSING = "READY_FOR_PROCESSING", "Ready for Processing"
    PROCESSING = "PROCESSING", "Processing"
    READY = "READY", "Ready"
    FAILED = "FAILED", "Failed"
    ARCHIVED = "ARCHIVED", "Archived"

class FileRole(models.TextChoices):
    QUESTION_BANK = "QUESTION_BANK", "Question Bank"
    NOTES = "NOTES", "Notes"


class UploadSessionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    VERIFYING = "VERIFYING", "Verifying"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"
    CLEANED = "CLEANED", "Cleaned"


class UploadFileStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    UPLOADED = "UPLOADED", "Uploaded"
    VERIFIED = "VERIFIED", "Verified"
    FAILED = "FAILED", "Failed"
    REGISTERED = "REGISTERED", "Registered"


class FileStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    PROCESSING = "PROCESSING", "Processing"
    ARCHIVED = "ARCHIVED", "Archived"
    DELETED = "DELETED", "Deleted"

class ProcessingStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    RUNNING = "RUNNING", "Running"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


class ProcessingStage(models.TextChoices):
    INITIALIZED = "INITIALIZED", "Initialized"
    DOWNLOADING = "DOWNLOADING", "Downloading Files"
    EXTRACTING = "EXTRACTING", "Extracting Content"
    VALIDATING = "VALIDATING", "Validating Data"
    PERSISTING = "PERSISTING", "Persisting Data"
    CLEANING_UP = "CLEANING_UP", "Cleaning Up"
    FINISHED = "FINISHED", "Finished"

