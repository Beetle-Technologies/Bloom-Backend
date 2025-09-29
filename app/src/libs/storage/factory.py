from typing import Any

from src.core.config import settings
from src.core.logging import get_logger
from src.libs.storage.interface import StorageInterface
from src.libs.storage.providers.cloudinary import CloudinaryStorage
from src.libs.storage.providers.local import LocalStorage
from src.libs.storage.providers.s3 import S3Storage
from src.libs.storage.schemas import CloudinaryConfiguration, LocalConfiguration, S3Configuration

logger = get_logger(__name__)


class StorageFactory:
    """
    Factory for creating storage providers.
    """

    _providers: dict[str, type[StorageInterface]] = {
        "local": LocalStorage,
        "s3": S3Storage,
        "cloudinary": CloudinaryStorage,
    }

    @classmethod
    def register_provider(cls, name: str, provider_class: type[StorageInterface]) -> None:
        cls._providers[name] = provider_class

    @classmethod
    def create_provider(cls, provider_type: str, config: Any) -> StorageInterface:
        """
        Create a provider instance.

        Args:
            provider_type: Type of provider to create
            config: Provider configuration

        Returns:
            An instance of the requested provider

        Raises:
            ValueError: If the provider type is not supported
        """
        if provider_type not in cls._providers:
            raise ValueError(f"Unsupported storage provider type: {provider_type}")

        provider_class = cls._providers[provider_type]
        return provider_class(config)  # type: ignore

    @classmethod
    def get_configured_provider(cls) -> StorageInterface:
        """
        Get the configured storage provider.

        Returns:
            An instance of the configured storage provider
        """
        provider_type = settings.FILE_STORAGE_BACKEND

        if provider_type == "local":
            config = LocalConfiguration(base_path=settings.FILE_STORAGE_MEDIA_ROOT)
            return cls.create_provider("local", config)
        elif provider_type == "s3":
            config = S3Configuration(
                bucket_name=settings.FILE_STORAGE_S3_BUCKET_NAME,  # type: ignore
                region_name=settings.FILE_STORAGE_S3_REGION_NAME,  # type: ignore
                access_key_id=settings.FILE_STORAGE_S3_ACCESS_KEY_ID,  # type: ignore
                secret_access_key=settings.FILE_STORAGE_S3_SECRET_ACCESS_KEY,  # type: ignore
                endpoint_url=settings.FILE_STORAGE_S3_ENDPOINT_URL,
            )
            return cls.create_provider("s3", config)
        elif provider_type == "cloudinary":
            config = CloudinaryConfiguration(
                cloud_name=settings.FILE_STORAGE_CLOUDINARY_CLOUD_NAME,  # type: ignore
                api_key=settings.FILE_STORAGE_CLOUDINARY_API_KEY,  # type: ignore
                api_secret=settings.FILE_STORAGE_CLOUDINARY_API_SECRET,  # type: ignore
            )
            return cls.create_provider("cloudinary", config)
        else:
            raise ValueError(f"Unsupported storage backend: {provider_type}")
