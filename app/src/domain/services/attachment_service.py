from __future__ import annotations

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from fastapi import UploadFile
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.config import settings
from src.core.constants import ALLOWED_MIME_TYPES
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.repositories.attachment_repository import AttachmentBlobRepository, AttachmentRepository
from src.domain.schemas.attachment import (
    AttachmentBlobCreate,
    AttachmentCreate,
    AttachmentDownloadResponse,
    AttachmentPresignedUrlResponse,
    AttachmentUploadResponse,
)
from src.libs.storage.utils import calculate_checksum, generate_file_key, generate_thumbnail, get_file_info, is_image

if TYPE_CHECKING:
    from src.libs.storage import StorageService

logger = get_logger(__name__)


class AttachmentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.attachment_repository = AttachmentRepository(session=self.session)
        self.blob_repository = AttachmentBlobRepository(session=self.session)

    async def upload_attachment(
        self,
        *,
        file: UploadFile,
        name: str,
        attachable_type: str,
        attachable_id: GUID,
        uploaded_by: GUID | None = None,
        tags: str | None = None,
        expires_at: datetime | None = None,
        auto_delete_after: str | None = None,
        storage_service: StorageService,
    ) -> AttachmentUploadResponse:
        """
        Upload an attachment file.

        Args:
            file: The uploaded file
            name: Name identifier for the attachment
            attachable_type: Type of the attachable entity
            attachable_id: ID of the attachable entity
            uploaded_by: ID of the user uploading
            tags: Tags for the attachment
            expires_at: Expiration date
            auto_delete_after: Auto delete configuration
            storage_service: The storage service instance

        Returns:
            AttachmentUploadResponse: The upload response
        """
        try:
            file_content = await file.read()

            if file.content_type not in ALLOWED_MIME_TYPES:
                raise errors.ServiceError(
                    detail=f"Unsupported file type: {file.content_type}",
                )

            if len(file_content) == 0:
                raise errors.ServiceError(
                    detail="Empty files are not allowed",
                )

            if len(file_content) > settings.FILE_MAX_SIZE:
                raise errors.ServiceError(
                    detail=f"File too large. Maximum size is {settings.FILE_MAX_SIZE} bytes",
                )

            mime_type, file_extension, file_size = get_file_info(file_content, file.filename or "")

            file_key = generate_file_key(file.filename or name, attachable_type, str(attachable_id))

            file_path = await storage_service.upload_file(file_content, file_key, mime_type)

            checksum = calculate_checksum(file_content)

            parsed_tags = None
            if tags:
                try:
                    parsed_tags = json.loads(tags)
                except json.JSONDecodeError:
                    parsed_tags = [tag.strip() for tag in tags.split(",")]

            blob_data = AttachmentBlobCreate(
                key=file_key,
                filename=file.filename or name,
                content_type=mime_type,
                service_name=settings.FILE_STORAGE_BACKEND,
                byte_size=Decimal(str(file_size)),
                checksum=checksum,
                meta_data={
                    "original_filename": file.filename,
                    "uploaded_by": uploaded_by,
                    "tags": parsed_tags,
                    "expires_at": expires_at.isoformat() if expires_at else None,
                    "auto_delete_after": auto_delete_after,
                },
            )

            blob = await self.blob_repository.create_blob(blob_data)

            attachment_data = AttachmentCreate(
                name=name,
                attachable_type=attachable_type,
                attachable_id=attachable_id,
                blob_id=blob.id,
            )

            attachment = await self.attachment_repository.create_attachment(attachment_data)

            file_url = await storage_service.get_file_url(file_key)

            thumbnail_url = None
            if is_image(mime_type) and settings.FILE_STORAGE_GENERATE_THUMBNAILS:
                thumbnail_content = await generate_thumbnail(file_content, mime_type)
                if thumbnail_content:
                    thumbnail_key = f"thumbnails-{file_key}"
                    try:
                        await storage_service.upload_file(thumbnail_content, thumbnail_key, "image/jpeg")
                        thumbnail_url = await storage_service.get_file_url(thumbnail_key)
                    except Exception as e:
                        logger.warning(f"Failed to generate thumbnail: {e}")

            return AttachmentUploadResponse(
                attachment_id=attachment.id,
                attachment_friendly_id=attachment.friendly_id,
                blob_id=blob.id,
                blob_friendly_id=blob.friendly_id,
                filename=file_key,
                original_filename=file.filename or name,
                file_size=Decimal(str(file_size)),
                mime_type=mime_type,
                file_extension=file_extension,
                file_path=file_path,
                file_url=file_url,
                thumbnail_url=thumbnail_url,
                attachable_type=attachable_type,
                attachable_id=attachable_id,
                tags=parsed_tags,
                uploaded_by=uploaded_by,
                expires_at=expires_at,
                auto_delete_after=auto_delete_after,
            )

        except errors.ServiceError as se:
            raise se
        except Exception as e:
            logger.exception(f"Error uploading attachment: {e}")
            raise errors.ServiceError(
                detail="Failed to upload attachment",
            ) from e

    async def generate_presigned_upload_url(
        self,
        *,
        filename: str,
        name: str,
        attachable_type: str,
        attachable_id: GUID,
        uploaded_by: str | None = None,
        expires_in: int = 3600,
        storage_service: StorageService,
    ) -> AttachmentPresignedUrlResponse:
        """
        Generate a presigned URL for attachment upload.

        Args:
            filename: The filename
            name: Name identifier
            attachable_type: Type of attachable entity
            attachable_id: ID of attachable entity
            uploaded_by: User uploading
            expires_in: URL expiration time
            storage_service: Storage service instance

        Returns:
            AttachmentPresignedUrlResponse: The presigned URL response
        """
        try:
            file_key = generate_file_key(filename, attachable_type, str(attachable_id))

            blob_data = AttachmentBlobCreate(
                key=file_key,
                filename=filename,
                content_type="application/octet-stream",
                service_name=settings.FILE_STORAGE_BACKEND,
                byte_size=Decimal("0"),
                checksum=None,
                meta_data={
                    "original_filename": filename,
                    "uploaded_by": str(uploaded_by) if uploaded_by else None,
                    "presigned": True,
                },
            )

            blob = await self.blob_repository.create_blob(blob_data)

            attachment_data = AttachmentCreate(
                name=name,
                attachable_type=attachable_type,
                attachable_id=attachable_id,
                blob_id=blob.id,
            )

            attachment = await self.attachment_repository.create_attachment(attachment_data)

            upload_url = await storage_service.generate_presigned_url(file_key, expires_in)

            return AttachmentPresignedUrlResponse(
                upload_url=upload_url,
                attachment_id=attachment.id,
                blob_id=blob.id,
                file_key=file_key,
                expires_at=datetime.now() + timedelta(seconds=expires_in),
            )

        except Exception as e:
            logger.exception(f"Error generating presigned upload URL: {e}")
            raise errors.ServiceError(
                detail="Failed to generate presigned upload URL",
            ) from e

    async def get_attachment_download_url(
        self,
        *,
        attachment_fid: str,
        storage_service: StorageService,
    ) -> AttachmentDownloadResponse:
        """
        Get a download URL for an attachment.

        Args:
            attachment_fid: The friendly ID of the attachment
            storage_service: Storage service instance

        Returns:
            AttachmentDownloadResponse: The download URL response
        """
        try:
            attachment = await self.attachment_repository.find_one_by_or_none(friendly_id=attachment_fid)
            if not attachment:
                raise errors.NotFoundError(detail="Attachment not found")

            blob = await self.blob_repository.find_one_by_or_none(id=attachment.blob_id)
            if not blob:
                raise errors.NotFoundError(detail="Attachment blob not found")

            download_url, expires_in = await storage_service.download_file_presigned(blob.key)

            return AttachmentDownloadResponse(
                download_url=download_url,
                attachment_id=attachment.id,
                file_key=blob.key,
                expires_at=expires_in.total_seconds(),
            )

        except errors.ServiceError as se:
            raise se
        except Exception as e:
            logger.exception(f"Error getting attachment download URL: {e}")
            raise errors.ServiceError(
                detail="Failed to get attachment download URL",
            ) from e

    async def delete_attachments(
        self,
        *,
        attachment_ids: list[GUID],
        storage_service: StorageService,
    ) -> bool:
        """
        Delete attachments and their associated files.

        Args:
            attachment_ids: List of attachment IDs to delete
            storage_service: Storage service instance

        Returns:
            bool: True if successful
        """
        try:
            for attachment_id in attachment_ids:
                attachment = await self.attachment_repository.find_one_by_or_none(id=attachment_id)
                if not attachment:
                    continue

                blob = await self.blob_repository.find_one_by_or_none(id=attachment.blob_id)
                if blob:
                    await storage_service.delete_file(blob.key)

                    await self.blob_repository.update(blob.id, {"deleted_datetime": datetime.now()})

                await self.attachment_repository.update(attachment.id, {"deleted_datetime": datetime.now()})

            return True

        except Exception as e:
            logger.exception(f"Error deleting attachments: {e}")
            raise errors.ServiceError(
                detail="Failed to delete attachments",
            ) from e

    async def delete_attachment(
        self,
        *,
        attachment_fid: str,
        account_id: GUID,
        storage_service: StorageService,
    ) -> bool:
        """
        Delete a single attachment.

        Args:
            attachment_fid: The friendly ID of the attachment
            account_id: The account ID (for permission checking)
            storage_service: Storage service instance

        Returns:
            bool: True if deleted
        """
        try:
            attachment = await self.attachment_repository.find_one_by_or_none(friendly_id=attachment_fid)
            if not attachment:
                return False

            # TODO: Add permission checking based on account_id

            blob = await self.blob_repository.find_one_by_or_none(id=attachment.blob_id)
            if blob:
                # Delete from storage
                await storage_service.delete_file(blob.key)

                await self.blob_repository.update(blob.id, {"deleted_datetime": datetime.now()})

            await self.attachment_repository.update(attachment.id, {"deleted_datetime": datetime.now()})

            return True

        except Exception as e:
            logger.exception(f"Error deleting attachment: {e}")
            raise errors.ServiceError(
                detail="Failed to delete attachment",
            ) from e

    async def replace_attachment(
        self,
        *,
        attachment_fid: str,
        file: UploadFile,
        uploaded_by: GUID | None = None,
        tags: str | None = None,
        expires_at: datetime | None = None,
        auto_delete_after: str | None = None,
        storage_service: StorageService,
    ) -> AttachmentUploadResponse:
        """
        Replace an existing attachment with a new file.

        Args:
            attachment_fid: The friendly ID of the attachment to replace
            file: The new file to upload
            uploaded_by: User uploading
            tags: Tags for the attachment
            expires_at: Expiration date
            auto_delete_after: Auto delete setting
            storage_service: Storage service instance

        Returns:
            AttachmentUploadResponse: The upload response
        """
        try:
            attachment = await self.attachment_repository.find_one_by_or_none(friendly_id=attachment_fid)
            if not attachment:
                raise errors.NotFoundError(detail="Attachment not found")

            blob = await self.blob_repository.find_one_by_or_none(id=attachment.blob_id)
            if not blob:
                raise errors.NotFoundError(detail="Attachment blob not found")

            file_content = await file.read()

            if file.content_type not in ALLOWED_MIME_TYPES:
                raise errors.ServiceError(
                    detail=f"Unsupported file type: {file.content_type}",
                )

            if len(file_content) == 0:
                raise errors.ServiceError(
                    detail="Empty files are not allowed",
                )

            if len(file_content) > settings.FILE_MAX_SIZE:
                raise errors.ServiceError(
                    detail=f"File too large. Maximum size is {settings.FILE_MAX_SIZE} bytes",
                )

            mime_type, file_extension, file_size = get_file_info(file_content, file.filename or attachment.name)

            parsed_tags = None
            if tags:
                try:
                    parsed_tags = json.loads(tags)
                except json.JSONDecodeError:
                    parsed_tags = [tag.strip() for tag in tags.split(",")]

            checksum = calculate_checksum(file_content)

            file_path = await storage_service.upload_file(file_content, blob.key, mime_type)

            blob_update = {
                "filename": file.filename or blob.filename,
                "content_type": mime_type,
                "byte_size": Decimal(str(file_size)),
                "checksum": checksum,
                "meta_data": {
                    "original_filename": file.filename,
                    "uploaded_by": str(uploaded_by) if uploaded_by else None,
                    "tags": parsed_tags,
                    "expires_at": expires_at.isoformat() if expires_at else None,
                    "auto_delete_after": auto_delete_after,
                    "replaced_at": datetime.now().isoformat(),
                },
            }
            await self.blob_repository.update(blob.id, blob_update)

            file_url = await storage_service.get_file_url(blob.key)

            thumbnail_url = None
            if is_image(mime_type) and settings.FILE_STORAGE_GENERATE_THUMBNAILS:
                thumbnail_content = await generate_thumbnail(file_content, mime_type)
                if thumbnail_content:
                    thumbnail_key = f"thumbnails-{blob.key}"
                    try:
                        await storage_service.upload_file(thumbnail_content, thumbnail_key, "image/jpeg")
                        thumbnail_url = await storage_service.get_file_url(thumbnail_key)
                    except Exception:
                        pass

            return AttachmentUploadResponse(
                attachment_id=attachment.id,
                attachment_friendly_id=attachment.friendly_id,
                blob_id=blob.id,
                blob_friendly_id=blob.friendly_id,
                filename=blob.key,
                original_filename=file.filename or blob.filename,
                file_size=Decimal(str(file_size)),
                mime_type=mime_type,
                file_extension=file_extension,
                file_path=file_path,
                file_url=file_url,
                thumbnail_url=thumbnail_url,
                attachable_type=attachment.attachable_type,
                attachable_id=attachment.attachable_id,
                tags=parsed_tags,
                uploaded_by=uploaded_by,
                expires_at=expires_at,
                auto_delete_after=auto_delete_after,
            )

        except errors.ServiceError as se:
            raise se
        except Exception as e:
            logger.exception(f"Error replacing attachment: {e}")
            raise errors.ServiceError(
                detail="Failed to replace attachment",
            ) from e
