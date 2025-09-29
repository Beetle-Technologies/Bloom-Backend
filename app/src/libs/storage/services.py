from datetime import timedelta

from src.core.types import FileContent
from src.libs.storage.factory import StorageFactory

provider = StorageFactory.get_configured_provider()


class StorageService:

    async def upload_file(
        self,
        file_data: FileContent,
        file_key: str,
        content_type: str,
    ) -> str:
        """
        Upload a file using the configured storage provider.

        Args:
            file_data (FileContent): The file data to upload.
            file_key (str): The key under which the file will be stored.
            content_type (str): The MIME type of the file.

        Returns:
            str: The key or path of the uploaded file.

        Raises:
            StorageUploadError: if uploading the file fails
        """

        return await provider.upload_file(file_data=file_data, file_key=file_key, content_type=content_type)

    async def download_file(self, file_key: str) -> bytes:
        """
        Download a file using the configured storage provider.

        Args:
            file_key (str): The key of the file to download.

        Returns:
            bytes: The content of the file.

        Raises:
            StorageDownloadError: if downloading the file fails
        """

        return await provider.download_file(file_key=file_key)

    async def delete_file(self, file_key: str) -> bool:
        """
        Delete a file using the configured storage provider.

        Args:
            file_key (str): The key of the file to delete.

        Returns:
            bool: True if the file was deleted, False if it did not exist.

        Raises:
            StorageDeleteError: if deleting the file fails
        """

        return await provider.delete_file(file_key=file_key)

    async def generate_presigned_url(
        self,
        file_key: str,
        expires_in: int | None = None,
    ) -> str:
        """
        Generate a presigned URL for accessing a file.

        Args:
            file_key (str): The key of the file.
            expires_in (int | None): The expiration time in seconds.

        Returns:
            str: The presigned URL.

        Raises:
            StorageError: if generating the URL fails
        """

        if expires_in is None:
            return await provider.generate_presigned_url(file_key=file_key)
        return await provider.generate_presigned_url(file_key=file_key, expires_in=expires_in)

    async def get_file_url(self, file_key: str) -> str:
        """
        Get the URL for accessing a file.

        Args:
            file_key (str): The key of the file.

        Returns:
            str: The URL to access the file.
        """

        return await provider.get_file_url(file_key=file_key)

    async def download_file_presigned(self, file_key: str) -> tuple[str, timedelta]:
        """
        Generate a presigned URL for downloading a file.

        Args:
            file_key (str): The key of the file to download.

        Returns:
            tuple[str, timedelta]: The presigned URL and its expiration time.
        """

        return await provider.download_file_presigned(file_key=file_key)

    async def generate_presigned_upload_url(
        self,
        file_key: str,
        expires_in: int | None = None,
    ) -> dict[str, str]:
        """
        Generate parameters for presigned upload.

        Args:
            file_key (str): The key under which the file will be stored.
            expires_in (int | None): The expiration time in seconds.

        Returns:
            dict: Parameters for presigned upload.
        """
        if expires_in is None:
            return await provider.generate_presigned_upload_url(file_key=file_key)
        return await provider.generate_presigned_upload_url(file_key=file_key, expires_in=expires_in)


storage_service = StorageService()
