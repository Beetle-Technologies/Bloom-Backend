from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import aiofiles
from src.core.config import settings
from src.core.types import FileContent
from src.libs.storage.interface import StorageInterface
from src.libs.storage.schemas import LocalConfiguration


class LocalStorage(StorageInterface):
    """
    Local file storage backend implementation.
    """

    def __init__(self, config: LocalConfiguration):
        self.base_path = Path(config.base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(self, file_data: FileContent, file_key: str, content_type: str) -> str:
        """
        Upload a file to the local storage.

        Args:
            file_data (BinaryIO): The file data to upload.
            file_key (str): The key under which the file will be stored.
            content_type (str): The MIME type of the file.

        Returns:
            str: The path to the uploaded file.
        """

        file_path = self.base_path / file_key
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, "wb") as f:
            if isinstance(file_data, (bytes, bytearray, memoryview)):
                await f.write(file_data)
            elif hasattr(file_data, "read"):
                content = file_data.read()
                if isinstance(content, (bytes, bytearray, memoryview)):
                    await f.write(content)
                elif content:
                    await f.write(str(content).encode())
            else:
                await f.write(str(file_data).encode())

        return str(file_path)

    async def download_file(self, file_key: str) -> bytes:
        """
        Download a file from the local storage.

        Args:
            file_key (str): The key of the file to download.

        Returns:
            bytes: The content of the file.
        """

        file_path = self.base_path / file_key
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_key} not found")

        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    async def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from the local storage.

        Args:
            file_key (str): The key of the file to delete.

        Returns:
            bool: True if the file was deleted, False if it did not exist.
        """

        file_path = self.base_path / file_key
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def generate_presigned_url(
        self,
        file_key: str,
        expires_in: int = settings.FILE_STORAGE_PRESIGNGED_EXPIRY_TIME,
    ) -> str:
        """
        Generate a presigned URL for accessing a file.

        Args:
            file_key (str): The key of the file.
            expires_in (int): The expiration time in seconds for the presigned URL.

        Returns:
            str: The presigned URL for accessing the file.
        """

        # For local storage, we'll return a regular URL since we don't have presigned URLs implementation.
        return await self.get_file_url(file_key)

    async def download_file_presigned(self, file_key: str) -> tuple[str, timedelta]:
        """
        Generate a presigned URL for downloading a file.

        Args:
            file_key (str): The key of the file to download.

        Returns:
            str: The presigned URL for downloading the file.
        """
        return (
            await self.get_file_url(file_key),
            timedelta(days=settings.FILE_STORAGE_PRESIGNGED_EXPIRY_TIME),
        )

    async def get_file_url(self, file_key: str) -> str:
        """
        Get the URL for accessing a file.

        Args:
            file_key (str): The key of the file.

        Returns:
            str: The URL to access the file.
        """
        return f"{settings.SERVER_URL}/media/{file_key}"

    async def generate_presigned_upload_url(
        self,
        file_key: str,
        expires_in: int = settings.FILE_STORAGE_PRESIGNGED_EXPIRY_TIME,
    ) -> dict[str, str]:
        """
        Generate parameters for presigned upload (not applicable for local storage).

        Args:
            file_key (str): The key under which the file will be stored.
            expires_in (int): The expiration time in seconds.

        Returns:
            dict: Empty dict since local storage doesn't support presigned uploads.
        """
        # Local storage doesn't support presigned uploads
        return {}
