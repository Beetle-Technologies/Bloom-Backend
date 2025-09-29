from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.session import get_db_session
from src.core.dependencies import api_rate_limit, is_bloom_client, requires_eligible_account
from src.core.exceptions import errors
from src.core.helpers.response import IResponseBase, build_json_response
from src.core.types import BloomClientInfo
from src.domain.schemas import (
    AccountBasicProfileResponse,
    AccountUpdate,
    AddressCreateRequest,
    AddressResponse,
    AddressUpdateRequest,
    AuthSessionState,
)
from src.domain.services import AccountService, AddressService

router = APIRouter()


@router.get(
    "/me",
    dependencies=[api_rate_limit],
    response_model=IResponseBase[AccountBasicProfileResponse],
)
async def me(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    auth_state: Annotated[AuthSessionState, requires_eligible_account],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IResponseBase[AccountBasicProfileResponse]:
    """
    Get current account information
    """
    try:
        account_service = AccountService(session)

        data = await account_service.get_profile_by(id=auth_state.id, type_info_id=auth_state.type_info_id)

        return build_json_response(data=data, message="Account profile retrieved successfully")

    except errors.ServiceError as se:
        raise se
    except Exception as e:
        raise errors.ServiceError(
            detail="Failed to retrieve current account profile",
            status=500,
        ) from e


@router.put(
    "/me",
    dependencies=[api_rate_limit],
    response_model=IResponseBase[AccountBasicProfileResponse],
)
async def update_me(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    auth_state: Annotated[AuthSessionState, requires_eligible_account],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    account_data: Annotated[AccountUpdate, Body(...)],
) -> IResponseBase[AccountBasicProfileResponse]:
    """
    Update current account information
    """
    try:
        account_service = AccountService(session)

        data = await account_service.update_profile_by(
            id=auth_state.id,
            type_info_id=auth_state.type_info_id,
            account_update=account_data,
        )

        assert isinstance(data, AccountBasicProfileResponse)

        return build_json_response(data=data, message="Account profile updated successfully")

    except errors.ServiceError as se:
        raise se
    except AssertionError as ae:
        raise errors.ServiceError(
            detail="Failed to update account profile",
            status=500,
        ) from ae
    except Exception as e:
        raise errors.ServiceError(
            detail="Failed to update account profile",
            status=500,
        ) from e


@router.delete("/me", dependencies=[api_rate_limit], response_model=IResponseBase[None])
async def delete_me(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    auth_state: Annotated[AuthSessionState, requires_eligible_account],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IResponseBase[None]:
    """
    Delete current account
    """
    try:
        account_service = AccountService(session)

        deleted = await account_service.mark_account_for_deletion(id=auth_state.id)

        if not deleted:
            raise errors.ServiceError(
                detail="Failed to delete account",
                status=500,
            )

        return build_json_response(data=None, message="Account deleted successfully")

    except errors.ServiceError as se:
        raise se
    except Exception as e:
        raise errors.ServiceError(
            detail="Failed to delete account",
            status=500,
        ) from e


@router.get(
    "/me/addresses",
    dependencies=[api_rate_limit],
    response_model=IResponseBase[list[AddressResponse]],
)
async def get_addresses(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    auth_state: Annotated[AuthSessionState, requires_eligible_account],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IResponseBase[list[AddressResponse]]:
    """
    Get current account addresses
    """
    try:
        address_service = AddressService(session)

        data = await address_service.get_addresses_for_account_type_info(account_type_info_id=auth_state.type_info_id)

        return build_json_response(data=data, message="Addresses retrieved successfully")

    except errors.ServiceError as se:
        raise se
    except Exception as e:
        raise errors.ServiceError(
            detail="Failed to retrieve addresses",
            status=500,
        ) from e


@router.post(
    "/me/addresses",
    dependencies=[api_rate_limit],
    response_model=IResponseBase[AddressResponse],
)
async def create_addresses(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    auth_state: Annotated[AuthSessionState, requires_eligible_account],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    address_data: Annotated[AddressCreateRequest, Body(...)],
) -> IResponseBase[AddressResponse]:
    """
    Create new address for current account
    """
    try:
        address_service = AddressService(session)

        created_address = await address_service.create_address_for_account_type_info(
            account_type_info_id=auth_state.type_info_id, address_request=address_data
        )

        assert created_address.friendly_id is not None

        address = await address_service.get_address_by_friendly_id(created_address.friendly_id, auth_state.type_info_id)

        assert address is not None

        data = AddressResponse.from_obj(address)

        return build_json_response(data=data, message="Address created successfully")

    except errors.ServiceError as se:
        raise se
    except Exception as e:
        raise errors.ServiceError(
            detail="Failed to create address",
            status=500,
        ) from e


@router.put(
    "/me/addresses/{address_fid}",
    dependencies=[api_rate_limit],
    response_model=IResponseBase[AddressResponse],
)
async def update_addresses(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    auth_state: Annotated[AuthSessionState, requires_eligible_account],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    address_fid: Annotated[str, Path(..., description="The Friendly ID of the address to update")],
    address_data: Annotated[AddressUpdateRequest, Body(...)],
) -> IResponseBase[AddressResponse]:
    """
    Update current account address
    """
    try:
        address_service = AddressService(session)

        updated_address = await address_service.update_address_for_account_type_info(
            address_friendly_id=address_fid,
            account_type_info_id=auth_state.type_info_id,
            address_request=address_data,
        )

        assert updated_address is not None

        assert updated_address.friendly_id is not None

        address = await address_service.get_address_by_friendly_id(updated_address.friendly_id, auth_state.type_info_id)

        data = AddressResponse.from_obj(address)

        return build_json_response(data=data, message="Address updated successfully")

    except errors.ServiceError as se:
        raise se
    except AssertionError as ae:
        raise errors.ServiceError(
            detail="Failed to update address",
            status=500,
        ) from ae
    except Exception as e:
        raise errors.ServiceError(
            detail="Failed to update address",
            status=500,
        ) from e


@router.delete(
    "/me/addresses/{address_fid}",
    dependencies=[api_rate_limit],
    response_model=IResponseBase[None],
)
async def delete_addresses(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    auth_state: Annotated[AuthSessionState, requires_eligible_account],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    address_fid: Annotated[str, Path(..., description="The Friendly ID of the address to delete")],
) -> IResponseBase[None]:
    """
    Delete current account specific address
    """
    try:
        address_service = AddressService(session)

        deleted = await address_service.delete_address_for_account_type_info(
            address_friendly_id=address_fid,
            account_type_info_id=auth_state.type_info_id,
        )

        if not deleted:
            raise errors.ServiceError(
                detail="Address not found or access denied",
                status=404,
            )

        return build_json_response(data=None, message="Address deleted successfully")

    except errors.ServiceError as se:
        raise se
    except Exception as e:
        raise errors.ServiceError(
            detail="Failed to delete address",
            status=500,
        ) from e
