from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import File, UploadFile
from pydantic import BaseModel, BeforeValidator, Field, field_validator, model_validator
from src.core.helpers import optional
from src.core.helpers.request import parse_list
from src.core.types import GUID


class AttachmentBase(BaseModel):
    """Base attachment schema with common fields."""

    name: str = Field(..., max_length=255, description="Name identifier for the attachment")
    attachable_type: str = Field(..., max_length=120, description="Type of the attachable entity")
    attachable_id: GUID = Field(..., description="ID of the attachable entity")


class AttachmentCreate(AttachmentBase):
    """Schema for creating a new attachment."""

    blob_id: GUID = Field(..., description="ID of the attachment blob")


@optional
class AttachmentUpdate(BaseModel):
    """Schema for updating an existing attachment."""

    name: str | None = Field(None, max_length=255, description="Name identifier for the attachment")


class AttachmentResponse(BaseModel):
    """Schema for attachment response data."""

    id: GUID
    friendly_id: str | None
    name: str
    attachable_type: str
    attachable_id: GUID
    blob_id: GUID
    created_datetime: datetime
    deleted_datetime: datetime | None


class AttachmentBlobBase(BaseModel):
    """Base attachment blob schema with common fields."""

    key: str = Field(..., max_length=255, description="Unique key to identify the blob")
    filename: str = Field(..., max_length=255, description="Name of the file")
    content_type: str = Field(..., max_length=100, description="MIME type of the file")
    service_name: str = Field(..., max_length=100, description="Storage service used")
    byte_size: Decimal = Field(..., description="Size of the file in bytes")
    checksum: str | None = Field(None, max_length=128, description="Checksum for integrity verification")


class AttachmentBlobCreate(AttachmentBlobBase):
    """Schema for creating a new attachment blob."""

    meta_data: dict | None = Field(None, description="Additional metadata about the file")


@optional
class AttachmentBlobUpdate(BaseModel):
    """Schema for updating an existing attachment blob."""

    filename: str | None = Field(None, max_length=255, description="Name of the file")
    meta_data: dict | None = Field(None, description="Additional metadata about the file")


class AttachmentBlobResponse(BaseModel):
    """Schema for attachment blob response data."""

    id: GUID
    friendly_id: str | None
    key: str
    filename: str
    content_type: str
    meta_data: dict | None
    service_name: str
    byte_size: Decimal
    checksum: str | None
    created_datetime: datetime
    deleted_datetime: datetime | None


class AttachmentUploadRequest(BaseModel):
    """
    Schema for the attachment upload request.
    """

    file: Annotated[UploadFile, File(description="File to be uploaded")]
    name: str = Field(..., max_length=255, description="Name identifier for the attachment")
    attachable_type: str = Field(..., max_length=120, description="Type of the attachable entity")
    attachable_id: GUID = Field(..., description="ID of the attachable entity")
    tags: str | None = None
    expires_at: datetime | None = None
    auto_delete_after: str | None = None

    @field_validator("expires_at", mode="before")
    @classmethod
    def validate_expires_at(cls, v):
        if v == "" or v is None:
            return None
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Invalid expires_at format. Use ISO format.")

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v):
        if v == "" or v is None:
            return None
        return v

    @field_validator("auto_delete_after", mode="before")
    @classmethod
    def validate_auto_delete_after(cls, v):
        if v == "" or v is None:
            return None
        return v


class AttachmentDirectUploadRequest(BaseModel):
    """
    Schema for the direct attachment upload request.
    """

    filename: str = Field(..., ge=1, description="Name of the file")
    name: str = Field(..., max_length=255, description="Name identifier for the attachment")
    attachable_type: str = Field(..., max_length=120, description="Type of the attachable entity")
    attachable_id: GUID = Field(..., description="ID of the attachable entity")
    expires_in: int = Field(3600, description="Expiration time in seconds for the presigned URL")


class AttachmentUploadResponse(BaseModel):
    """
    Schema for the attachment upload response.
    """

    attachment_id: GUID
    attachment_friendly_id: str | None
    blob_id: GUID
    blob_friendly_id: str | None
    filename: str
    original_filename: str
    file_size: Decimal
    mime_type: str
    file_extension: str | None
    file_path: str
    file_url: str
    thumbnail_url: str | None = None
    attachable_type: str
    attachable_id: GUID
    tags: list[str] | None = None
    uploaded_by: GUID | None = None
    expires_at: datetime | None = None
    auto_delete_after: str | None = None


class AttachmentDeleteRequest(BaseModel):
    """
    Schema for the attachment delete request.
    """

    attachment_ids: list[GUID]


class AttachmentPresignedUrlResponse(BaseModel):
    """
    Schema for the response containing a presigned URL for attachment upload.
    """

    upload_url: str
    attachment_id: GUID
    blob_id: GUID
    file_key: str
    expires_at: datetime

    def to_url(self) -> str:
        return self.upload_url


class AttachmentDownloadResponse(BaseModel):
    """
    Schema for the response containing a presigned URL for attachment download.
    """

    download_url: str
    attachment_id: GUID
    file_key: str
    expires_at: float

    def to_url(self) -> str:
        return self.download_url


class AttachmentReplaceRequest(BaseModel):
    """
    Schema for the attachment replace request.
    """

    file: Annotated[UploadFile, File(description="File to be uploaded")]
    tags: str | None = None
    expires_at: datetime | None = None
    auto_delete_after: str | None = None

    @field_validator("expires_at", mode="before")
    @classmethod
    def validate_expires_at(cls, v):
        if v == "" or v is None:
            return None
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Invalid expires_at format. Use ISO format.")


class AttachmentBulkUploadRequest(BaseModel):
    """
    Schema for the bulk attachment upload request.
    """

    files: list[Annotated[UploadFile, File(description="Files to be uploaded")]]
    names: Annotated[list[str], BeforeValidator(parse_list())] = Field(
        ..., description="Comma separated string identifiers for the attachments"
    )
    attachable_type: str = Field(
        ...,
        max_length=120,
        description="Type of the attachable entity e.g., 'Account', 'Product', 'ProductItem",
    )
    attachable_id: GUID = Field(..., description="ID of the attachable entity")
    tags: str | None = None
    expires_at: datetime | None = None
    auto_delete_after: str | None = None

    @field_validator("expires_at", mode="before")
    @classmethod
    def validate_expires_at(cls, v):
        if v == "" or v is None:
            return None
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Invalid expires_at format. Use ISO format.")

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v):
        if v == "" or v is None:
            return None
        return v

    @field_validator("auto_delete_after", mode="before")
    @classmethod
    def validate_auto_delete_after(cls, v):
        if v == "" or v is None:
            return None
        return v

    @model_validator(mode="after")
    def validate_files_not_empty_and_names_length(self):
        if not self.files or len(self.files) == 0:
            raise ValueError("At least one file must be provided for bulk upload")

        if len(self.names) != len(self.files):
            raise ValueError("Number of names must match number of files")
        return self


class AttachmentBulkDirectUploadRequest(BaseModel):
    """
    Schema for the bulk direct attachment upload request.
    """

    filenames: list[str] = Field(..., description="Names of the files")
    names: Annotated[list[str], BeforeValidator(parse_list())] = Field(
        ..., description="Name identifiers for the attachments"
    )
    attachable_type: str = Field(..., max_length=120, description="Type of the attachable entity")
    attachable_id: GUID = Field(..., description="ID of the attachable entity")
    expires_in: int = Field(3600, description="Expiration time in seconds for the presigned URLs")

    @field_validator("names")
    @classmethod
    def validate_names_length(cls, v, info):
        if "filenames" in info.data and len(v) != len(info.data["filenames"]):
            raise ValueError("Number of names must match number of filenames")
        return v


class AttachmentBulkUploadResponse(BaseModel):
    """
    Schema for the bulk attachment upload response.
    """

    uploads: list[AttachmentUploadResponse]


class AttachmentBulkDirectUploadResponse(BaseModel):
    """
    Schema for the bulk direct attachment upload response.
    """

    uploads: list[AttachmentPresignedUrlResponse]


class AttachmentBasicResponse(BaseModel):
    """Schema for basic attachment response data."""

    id: GUID
    fid: str
    url: str | None


class AttachmentVariantCreate(BaseModel):
    """Schema for creating attachment variants."""

    blob_id: GUID
    variation_digest: str


class AttachmentVariantUpdate(BaseModel):
    """Schema for updating attachment variants."""

    variation_digest: str | None = None
