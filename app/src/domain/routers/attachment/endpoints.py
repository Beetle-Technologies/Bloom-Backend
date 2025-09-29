from io import BytesIO
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, Form, Path, Request
from fastapi.responses import StreamingResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.session import get_db_session
from src.core.dependencies import (
    api_rate_limit,
    get_storage_service,
    is_bloom_client,
    medium_api_rate_limit,
    requires_eligible_account,
    upload_rate_limit,
)
from src.core.exceptions import errors
from src.core.helpers.response import IResponseBase, build_json_response
from src.core.types import BloomClientInfo
from src.domain.schemas import AuthSessionState
from src.domain.schemas.attachment import (
    AttachmentBulkDirectUploadRequest,
    AttachmentBulkDirectUploadResponse,
    AttachmentBulkUploadRequest,
    AttachmentBulkUploadResponse,
    AttachmentDirectUploadRequest,
    AttachmentDownloadResponse,
    AttachmentPresignedUrlResponse,
    AttachmentReplaceRequest,
    AttachmentUploadRequest,
    AttachmentUploadResponse,
)
from src.domain.services import AttachmentService

from app.src.libs.storage.utils import get_file_info

if TYPE_CHECKING:
    from src.libs.storage import StorageService


router = APIRouter()


@router.post(
    "/upload",
    dependencies=[upload_rate_limit],
    response_model=IResponseBase[AttachmentUploadResponse],
)
async def upload_attachment(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    auth_state: Annotated[AuthSessionState, requires_eligible_account],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    storage_service: Annotated["StorageService", Depends(get_storage_service)],
    upload_data: Annotated[AttachmentUploadRequest, Form(..., media_type="multipart/form-data")],
) -> IResponseBase[AttachmentUploadResponse]:
    """
    Upload an attachment
    """
    try:
        attachment_service = AttachmentService(session)

        data = await attachment_service.upload_attachment(
            file=upload_data.file,
            name=upload_data.name,
            attachable_type=upload_data.attachable_type,
            attachable_id=upload_data.attachable_id,
            uploaded_by=auth_state.id,
            tags=upload_data.tags,
            expires_at=upload_data.expires_at,
            auto_delete_after=upload_data.auto_delete_after,
            storage_service=storage_service,
        )

        return build_json_response(data=data, message="Attachment uploaded successfully")

    except errors.ServiceError as se:
        raise se
    except Exception as e:
        raise errors.ServiceError(
            detail="Failed to upload attachment",
            status=500,
        ) from e


router.post(
    "/bulk_upload",
    dependencies=[upload_rate_limit],
    response_model=IResponseBase[AttachmentBulkUploadResponse],
)


async def bulk_upload_attachments(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    auth_state: Annotated[AuthSessionState, requires_eligible_account],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    storage_service: Annotated["StorageService", Depends(get_storage_service)],
    upload_data: Annotated[AttachmentBulkUploadRequest, Form(..., media_type="multipart/form-data")],
) -> IResponseBase[AttachmentBulkUploadResponse]:
    """
    Bulk upload multiple attachments
    """
    try:
        attachment_service = AttachmentService(session)

        uploads = []
        for file, name in zip(upload_data.files, upload_data.names):
            data = await attachment_service.upload_attachment(
                file=file,
                name=name,
                attachable_type=upload_data.attachable_type,
                attachable_id=upload_data.attachable_id,
                uploaded_by=auth_state.id,
                tags=upload_data.tags,
                expires_at=upload_data.expires_at,
                auto_delete_after=upload_data.auto_delete_after,
                storage_service=storage_service,
            )
            uploads.append(data)

        return build_json_response(
            data=AttachmentBulkUploadResponse(uploads=uploads),
            message="Attachments uploaded successfully",
        )

    except errors.ServiceError as se:
        raise se
    except Exception as e:
        raise errors.ServiceError(
            detail="Failed to upload attachments",
            status=500,
        ) from e


@router.post(
    "/direct_upload",
    dependencies=[upload_rate_limit],
    response_model=IResponseBase[AttachmentPresignedUrlResponse],
)
async def upload_direct_attachment(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    auth_state: Annotated[AuthSessionState, requires_eligible_account],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    storage_service: Annotated["StorageService", Depends(get_storage_service)],
    upload_data: Annotated[AttachmentDirectUploadRequest, Form(..., media_type="multipart/form-data")],
) -> IResponseBase[AttachmentPresignedUrlResponse]:
    """
    Upload an attachment directly to storage (bypassing the server)

    This endpoint provides a pre-signed URL for direct upload to the storage service.
    """
    try:
        attachment_service = AttachmentService(session)

        data = await attachment_service.generate_presigned_upload_url(
            filename=upload_data.filename,
            name=upload_data.name,
            attachable_type=upload_data.attachable_type,
            attachable_id=upload_data.attachable_id,
            uploaded_by=auth_state.id,  # type: ignore
            expires_in=upload_data.expires_in,
            storage_service=storage_service,
        )

        return build_json_response(data=data, message="Presigned upload URL generated successfully")

    except errors.ServiceError as se:
        raise se
    except Exception as e:
        raise errors.ServiceError(
            detail="Failed to generate presigned upload URL",
            status=500,
        ) from e


@router.post(
    "/bulk_direct_upload",
    dependencies=[upload_rate_limit],
    response_model=IResponseBase[AttachmentBulkDirectUploadResponse],
)
async def bulk_direct_upload_attachments(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    auth_state: Annotated[AuthSessionState, requires_eligible_account],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    storage_service: Annotated["StorageService", Depends(get_storage_service)],
    upload_data: Annotated[AttachmentBulkDirectUploadRequest, Form(...)],
) -> IResponseBase[AttachmentBulkDirectUploadResponse]:
    """
    Bulk generate presigned URLs for direct upload of multiple attachments
    """
    try:
        attachment_service = AttachmentService(session)

        uploads = []
        for filename, name in zip(upload_data.filenames, upload_data.names):
            data = await attachment_service.generate_presigned_upload_url(
                filename=filename,
                name=name,
                attachable_type=upload_data.attachable_type,
                attachable_id=upload_data.attachable_id,
                uploaded_by=auth_state.id,
                expires_in=upload_data.expires_in,
                storage_service=storage_service,
            )
            uploads.append(data)

        return build_json_response(
            data=AttachmentBulkDirectUploadResponse(uploads=uploads),
            message="Presigned upload URLs generated successfully",
        )

    except errors.ServiceError as se:
        raise se
    except Exception as e:
        raise errors.ServiceError(
            detail="Failed to generate presigned upload URLs",
            status=500,
        ) from e


@router.delete(
    "/{attachment_fid}",
    dependencies=[medium_api_rate_limit],
    response_model=IResponseBase[None],
)
async def delete_attachment(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    attachment_fid: Annotated[str, Path(..., description="The Friendly ID of the attachment to delete")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, requires_eligible_account],
    storage_service: Annotated["StorageService", Depends(get_storage_service)],
) -> IResponseBase[None]:
    """
    Delete an attachment
    """
    try:
        attachment_service = AttachmentService(session)

        deleted = await attachment_service.delete_attachment(
            attachment_fid=attachment_fid,
            account_id=auth_state.id,
            storage_service=storage_service,
        )

        if not deleted:
            raise errors.ServiceError(
                detail="Attachment not found or access denied",
                status=404,
            )

        return build_json_response(data=None, message="Attachment deleted successfully")

    except errors.ServiceError as se:
        raise se
    except Exception as e:
        raise errors.ServiceError(
            detail="Failed to delete attachment",
            status=500,
        ) from e


@router.post(
    "/{attachment_fid}/download",
    dependencies=[api_rate_limit],
    response_model=IResponseBase[AttachmentDownloadResponse],
)
async def download_attachment(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    attachment_fid: Annotated[str, Path(..., description="The Friendly ID of the attachment to download")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, requires_eligible_account],  # noqa: ARG001
    storage_service: Annotated["StorageService", Depends(get_storage_service)],
) -> IResponseBase[AttachmentDownloadResponse]:
    """
    Download an attachment
    """
    try:
        attachment_service = AttachmentService(session)

        data = await attachment_service.get_attachment_download_url(
            attachment_fid=attachment_fid,
            storage_service=storage_service,
        )

        return build_json_response(data=data, message="Download URL generated successfully")

    except errors.ServiceError as se:
        raise se
    except Exception as e:
        raise errors.ServiceError(
            detail="Failed to get attachment download URL",
            status=500,
        ) from e


@router.get(
    "/{attachment_fid}/direct_download",
    dependencies=[api_rate_limit],
)
async def get_direct_attachment_url(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    attachment_fid: Annotated[str, Path(..., description="The Friendly ID of the attachment")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, requires_eligible_account],
    storage_service: Annotated["StorageService", Depends(get_storage_service)],
) -> StreamingResponse:
    """
    Get a pre-signed URL for direct download of an attachment from storage
    """
    try:
        attachment_service = AttachmentService(session)

        attachment = await attachment_service.attachment_repository.find_one_by_or_none(friendly_id=attachment_fid)
        if not attachment:
            raise errors.NotFoundError(detail="Attachment not found")

        blob = await attachment_service.blob_repository.find_one_by_or_none(id=attachment.blob_id)
        if not blob:
            raise errors.NotFoundError(detail="Attachment blob not found")

        file_content = await storage_service.download_file(blob.key)

        content_type, _, _ = get_file_info(file_content, blob.filename)

        return StreamingResponse(
            BytesIO(file_content),
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={blob.filename}",
                "Cache-Control": "public, max-age=3600",
            },
        )

    except errors.ServiceError as se:
        raise se
    except Exception as e:
        raise errors.ServiceError(
            detail="Failed to download attachment",
            status=500,
        ) from e


@router.post(
    "/{attachment_fid}/replace",
    dependencies=[medium_api_rate_limit],
    response_model=IResponseBase[AttachmentUploadResponse],
)
async def replace_attachment(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    attachment_fid: Annotated[str, Path(..., description="The Friendly ID of the attachment to replace")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, requires_eligible_account],
    storage_service: Annotated["StorageService", Depends(get_storage_service)],
    replace_data: Annotated[AttachmentReplaceRequest, Form(..., media_type="multipart/form-data")],
) -> IResponseBase[AttachmentUploadResponse]:
    """
    Replace an attachment
    """
    try:
        attachment_service = AttachmentService(session)

        data = await attachment_service.replace_attachment(
            attachment_fid=attachment_fid,
            file=replace_data.file,
            uploaded_by=auth_state.id,
            tags=replace_data.tags,
            expires_at=replace_data.expires_at,
            auto_delete_after=replace_data.auto_delete_after,
            storage_service=storage_service,
        )

        return build_json_response(data=data, message="Attachment replaced successfully")

    except errors.ServiceError as se:
        raise se
    except Exception as e:
        raise errors.ServiceError(
            detail="Failed to replace attachment",
            status=500,
        ) from e
