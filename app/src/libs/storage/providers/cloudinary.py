from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

import cloudinary
import cloudinary.uploader
import cloudinary.utils
import httpx
from src.core.config import settings
from src.core.types import FileContent
from src.libs.storage.exceptions import StorageDeleteError, StorageDownloadError, StorageError, StorageUploadError
from src.libs.storage.interface import StorageInterface
from src.libs.storage.schemas import CloudinaryConfiguration


class CloudinaryStorage(StorageInterface):
    """
    Cloudinary file storage backend implementation.
    """

    def __init__(self, config: CloudinaryConfiguration):
        self.config = config
        cloudinary.config(
            cloud_name=config.cloud_name,
            api_key=config.api_key,
            api_secret=config.api_secret,
        )

    async def upload_file(self, file_data: FileContent, file_key: str, content_type: str) -> str:
        """
        Upload a file to Cloudinary.

        Args:
            file_data (FileContent): The file data to upload.
            file_key (str): The key under which the file will be stored.
            content_type (str): The MIME type of the file.

        Returns:
            str: The public ID of the uploaded file.
        """
        try:
            if isinstance(file_data, bytes):
                file_obj = file_data
            elif hasattr(file_data, "read"):
                if hasattr(file_data, "seek"):
                    file_data.seek(0)  # type: ignore
                file_obj = file_data  # type: ignore
            else:
                file_obj = str(file_data).encode()

            result = cloudinary.uploader.upload(
                file_obj,
                public_id=file_key,
                resource_type="auto",
            )

            return result["public_id"]
        except Exception as e:
            raise StorageUploadError(detail=f"Failed to upload file to Cloudinary: {str(e)}")

    async def download_file(self, file_key: str) -> bytes:
        """
        Download a file from Cloudinary.

        Args:
            file_key (str): The key of the file to download.

        Returns:
            bytes: The content of the file.
        """
        try:
            url = await self.get_file_url(file_key)
            response = httpx.get(url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise StorageDownloadError(detail=f"Failed to download file from Cloudinary: {str(e)}")

    async def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from Cloudinary.

        Args:
            file_key (str): The key of the file to delete.

        Returns:
            bool: True if the file was deleted, False if it did not exist.
        """
        try:
            result = cloudinary.uploader.destroy(file_key)
            return result.get("result") == "ok"
        except Exception as e:
            raise StorageDeleteError(detail=f"Failed to delete file from Cloudinary: {str(e)}")

    async def generate_presigned_url(
        self,
        file_key: str,
        expires_in: int = settings.FILE_STORAGE_PRESIGNGED_EXPIRY_TIME,
    ) -> str:
        """
        Generate a URL for accessing a file in Cloudinary.

        Args:
            file_key (str): The key of the file.
            expires_in (int): The expiration time in seconds (not applicable for Cloudinary).

        Returns:
            str: The URL for accessing the file.
        """
        return await self.get_file_url(file_key)

    async def get_file_url(self, file_key: str) -> str:
        """
        Get the URL for accessing a file in Cloudinary.

        Args:
            file_key (str): The key of the file.

        Returns:
            str: The URL to access the file.
        """
        return f"https://res.cloudinary.com/{self.config.cloud_name}/image/upload/{file_key}"

    async def download_file_presigned(self, file_key: str) -> tuple[str, timedelta]:
        """
        Generate a URL for downloading a file from Cloudinary.

        Args:
            file_key (str): The key of the file to download.

        Returns:
            tuple[str, timedelta]: The URL and a long expiration time.
        """
        url = await self.get_file_url(file_key)
        return url, timedelta(days=365)

    async def generate_presigned_upload_url(
        self,
        file_key: str,
        expires_in: int = settings.FILE_STORAGE_PRESIGNGED_EXPIRY_TIME,
    ) -> dict[str, str]:
        """
        Generate parameters for signed upload to Cloudinary.

        Args:
            file_key (str): The key under which the file will be stored.
            expires_in (int): The expiration time in seconds.

        Returns:
            dict: Parameters for signed upload including signature, timestamp, etc.
        """
        try:
            timestamp = int(datetime.now().timestamp()) + expires_in

            # Generate signature
            params_to_sign = {
                "timestamp": timestamp,
                "public_id": file_key,
                "upload_preset": getattr(settings, "FILE_STORAGE_CLOUDINARY_UPLOAD_PRESET", None),
            }

            # Remove None values
            params_to_sign = {k: v for k, v in params_to_sign.items() if v is not None}

            # Create signature string
            signature_string = "&".join([f"{k}={v}" for k, v in sorted(params_to_sign.items())])
            signature_string += self.config.api_secret

            signature = hashlib.sha1(signature_string.encode()).hexdigest()

            upload_params = {
                "api_key": self.config.api_key,
                "timestamp": str(timestamp),
                "signature": signature,
                "public_id": file_key,
                "upload_url": f"https://api.cloudinary.com/v1_1/{self.config.cloud_name}/image/upload",
            }

            if (
                hasattr(settings, "FILE_STORAGE_CLOUDINARY_UPLOAD_PRESET")
                and settings.FILE_STORAGE_CLOUDINARY_UPLOAD_PRESET
            ):
                upload_params["upload_preset"] = settings.FILE_STORAGE_CLOUDINARY_UPLOAD_PRESET

            return upload_params

        except Exception as e:
            raise StorageError(detail=f"Failed to generate signed upload parameters: {str(e)}")
