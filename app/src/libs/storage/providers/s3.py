from __future__ import annotations

from datetime import timedelta

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from src.core.config import settings
from src.core.types import FileContent
from src.libs.storage.exceptions import (
    StorageDeleteError,
    StorageDownloadError,
    StorageError,
    StorageFileNotFoundError,
    StorageUploadError,
)
from src.libs.storage.interface import StorageInterface
from src.libs.storage.schemas import S3Configuration


class S3Storage(StorageInterface):
    """
    S3 file storage backend implementation.
    """

    def __init__(self, config: S3Configuration):
        self.config = config
        self.client = boto3.client(
            "s3",
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region_name,
            endpoint_url=config.endpoint_url,
        )
        self.bucket_name = config.bucket_name

    async def upload_file(self, file_data: FileContent, file_key: str, content_type: str) -> str:
        """
        Upload a file to S3.

        Args:
            file_data (FileContent): The file data to upload.
            file_key (str): The key under which the file will be stored.
            content_type (str): The MIME type of the file.

        Returns:
            str: The S3 key of the uploaded file.
        """
        try:
            if isinstance(file_data, bytes):
                body = file_data
            elif hasattr(file_data, "read"):
                if hasattr(file_data, "seek"):
                    file_data.seek(0)  # type: ignore
                body = file_data.read()  # type: ignore
                if isinstance(body, str):
                    body = body.encode()
            else:
                body = str(file_data).encode()

            self.client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=body,
                ContentType=content_type,
            )

            return file_key
        except (ClientError, NoCredentialsError) as e:
            raise StorageUploadError(detail=f"Failed to upload file to S3: {str(e)}")

    async def download_file(self, file_key: str) -> bytes:
        """
        Download a file from S3.

        Args:
            file_key (str): The key of the file to download.

        Returns:
            bytes: The content of the file.
        """
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=file_key)
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise StorageFileNotFoundError(detail=f"File {file_key} not found in S3")
            raise StorageDownloadError(detail=f"Failed to download file from S3: {str(e)}")

    async def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from S3.

        Args:
            file_key (str): The key of the file to delete.

        Returns:
            bool: True if the file was deleted, False if it did not exist.
        """
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return False
            raise StorageDeleteError(detail=f"Failed to delete file from S3: {str(e)}")

    async def generate_presigned_url(
        self,
        file_key: str,
        expires_in: int = settings.FILE_STORAGE_PRESIGNGED_EXPIRY_TIME,
    ) -> str:
        """
        Generate a presigned URL for accessing a file in S3.

        Args:
            file_key (str): The key of the file.
            expires_in (int): The expiration time in seconds for the presigned URL.

        Returns:
            str: The presigned URL for accessing the file.
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": file_key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            raise StorageError(detail=f"Failed to generate presigned URL: {str(e)}")

    async def get_file_url(self, file_key: str) -> str:
        """
        Get the public URL for accessing a file in S3.

        Args:
            file_key (str): The key of the file.

        Returns:
            str: The public URL to access the file.
        """
        if self.config.endpoint_url:
            return f"{self.config.endpoint_url}/{self.bucket_name}/{file_key}"
        else:
            return f"https://{self.bucket_name}.s3.{self.config.region_name}.amazonaws.com/{file_key}"

    async def download_file_presigned(self, file_key: str) -> tuple[str, timedelta]:
        """
        Generate a presigned URL for downloading a file from S3.

        Args:
            file_key (str): The key of the file to download.

        Returns:
            tuple[str, timedelta]: The presigned URL and its expiration time.
        """
        expires_in = settings.FILE_STORAGE_PRESIGNGED_EXPIRY_TIME
        url = await self.generate_presigned_url(file_key, expires_in)
        return url, timedelta(seconds=expires_in)

    async def generate_presigned_upload_url(
        self,
        file_key: str,
        expires_in: int = settings.FILE_STORAGE_PRESIGNGED_EXPIRY_TIME,
    ) -> dict[str, str]:
        """
        Generate a presigned URL for uploading a file to S3.

        Args:
            file_key (str): The key under which the file will be stored.
            expires_in (int): The expiration time in seconds.

        Returns:
            dict: Parameters for presigned upload including the URL and fields.
        """
        try:
            response = self.client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=file_key,
                ExpiresIn=expires_in,
            )
            return {
                "upload_url": response["url"],
                "fields": response["fields"],
            }
        except (ClientError, NoCredentialsError) as e:
            raise StorageError(detail=f"Failed to generate presigned upload URL: {str(e)}")
