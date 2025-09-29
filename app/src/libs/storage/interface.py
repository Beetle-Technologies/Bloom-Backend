from abc import ABC, abstractmethod
from datetime import timedelta

from src.core.config import settings
from src.core.types import FileContent


class StorageInterface(ABC):
    """
    Abstract base class for file storage backends.
    """

    @abstractmethod
    async def upload_file(self, file_data: FileContent, file_key: str, content_type: str) -> str:
        pass

    @abstractmethod
    async def download_file(self, file_key: str) -> bytes:
        pass

    @abstractmethod
    async def delete_file(self, file_key: str) -> bool:
        pass

    @abstractmethod
    async def generate_presigned_url(
        self,
        file_key: str,
        expires_in: int = settings.FILE_STORAGE_PRESIGNGED_EXPIRY_TIME,
    ) -> str:
        pass

    @abstractmethod
    async def get_file_url(self, file_key: str) -> str:
        pass

    @abstractmethod
    async def download_file_presigned(self, file_key: str) -> tuple[str, timedelta]:
        pass

    @abstractmethod
    async def generate_presigned_upload_url(
        self,
        file_key: str,
        expires_in: int = settings.FILE_STORAGE_PRESIGNGED_EXPIRY_TIME,
    ) -> dict[str, str]:
        pass
