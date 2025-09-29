from fastapi import status
from src.core.exceptions import errors


class StorageError(errors.ServiceError):
    """Base error for storage related issues"""

    type_ = "storage_error"
    title = "Storage Error"
    detail = "An error occurred in the storage service."
    status = status.HTTP_500_INTERNAL_SERVER_ERROR


class StorageUploadError(StorageError):
    """Raised when there is an error uploading a file."""

    title = "Storage Upload Error"
    detail = "There was an error uploading the file."
    status = status.HTTP_400_BAD_REQUEST


class StorageDownloadError(StorageError):
    """Raised when there is an error downloading a file."""

    title = "Storage Download Error"
    detail = "There was an error downloading the file."
    status = status.HTTP_400_BAD_REQUEST


class StorageDeleteError(StorageError):
    """Raised when there is an error deleting a file."""

    title = "Storage Delete Error"
    detail = "There was an error deleting the file."
    status = status.HTTP_400_BAD_REQUEST


class StorageFileNotFoundError(StorageError):
    """Raised when a file is not found."""

    title = "File Not Found"
    detail = "The requested file was not found."
    status = status.HTTP_404_NOT_FOUND


class StorageConfigurationError(StorageError):
    """Raised when there is a configuration error."""

    title = "Storage Configuration Error"
    detail = "The storage service is not configured correctly."
    status = status.HTTP_500_INTERNAL_SERVER_ERROR
