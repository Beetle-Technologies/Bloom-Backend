from __future__ import annotations

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.models.address import Address
from src.domain.repositories import AddressRepository
from src.domain.schemas import AddressCreate, AddressCreateRequest, AddressUpdate, AddressUpdateRequest
from src.domain.schemas.address import AddressResponse
from src.libs.query_engine.schemas import BaseQueryEngineParams, GeneralPaginationRequest

logger = get_logger(__name__)


class AddressService:
    """Service for managing addresses."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.address_repository = AddressRepository(session=self.session)

    async def get_addresses_for_account_type_info(self, account_type_info_id: GUID) -> list[AddressResponse]:
        """
        Get all addresses for an account type info.

        Args:
            account_type_info_id (GUID): The account type info ID

        Returns:
            list[AddressResponse]: List of addresses
        """
        try:
            result = await self.address_repository.find(
                pagination=GeneralPaginationRequest(
                    page=1,
                    filters={
                        "addressable_type__eq": "AccountTypeInfo",
                        "addressable_id__eq": account_type_info_id,
                    },
                    include=["country"],
                )
            )

            data = [AddressResponse.from_obj(addr) for addr in result.items]
            return data
        except errors.DatabaseError as de:
            logger.error(
                f"DatabaseError getting addresses for account type info {account_type_info_id}: {de.detail}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to retrieve addresses") from de
        except Exception as e:
            logger.error(
                f"Unexpected error getting addresses for account type info {account_type_info_id}: {str(e)}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to retrieve addresses") from e

    async def get_address_by_friendly_id(self, friendly_id: str, account_type_info_id: GUID) -> Address | None:
        """
        Get an address by friendly ID, ensuring it belongs to the account type info.

        Args:
            friendly_id (str): The friendly ID of the address
            account_type_info_id (GUID): The account type info ID for validation

        Returns:
            Address | None: The address if found and belongs to the account, None otherwise
        """
        try:
            address = await self.address_repository.query(
                params=BaseQueryEngineParams(
                    filters={
                        "friendly_id__eq": friendly_id,
                        "addressable_type__eq": "AccountTypeInfo",
                        "addressable_id__eq": account_type_info_id,
                    },
                    include=["country"],
                )
            )

            return address
        except errors.DatabaseError as de:
            logger.error(
                f"DatabaseError getting address by friendly_id {friendly_id}: {de.detail}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to retrieve address") from de
        except Exception as e:
            logger.error(
                f"Unexpected error getting address by friendly_id {friendly_id}: {str(e)}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to retrieve address") from e

    async def create_address_for_account_type_info(
        self,
        account_type_info_id: GUID,
        address_request: AddressCreateRequest,
    ) -> Address:
        """
        Create an address for an account type info.

        Args:
            account_type_info_id (GUID): The account type info ID
            address_request (AddressCreateRequest): The address creation request

        Returns:
            Address: The created address
        """
        try:
            address_create = AddressCreate(
                addressable_type="AccountTypeInfo",
                addressable_id=account_type_info_id,
                phone_number=address_request.phone_number,
                address=address_request.address,
                city=address_request.city,
                state=address_request.state,
                postal_code=address_request.postal_code,
                country_id=address_request.country_id,
                is_default=address_request.is_default,
            )

            return await self.address_repository.create(address_create)
        except errors.DatabaseError as de:
            logger.error(
                f"DatabaseError creating address for account type info {account_type_info_id}: {de.detail}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to create address") from de
        except errors.ServiceError:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error creating address for account type info {account_type_info_id}: {str(e)}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to create address") from e

    async def update_address_for_account_type_info(
        self,
        address_friendly_id: str,
        account_type_info_id: GUID,
        address_request: AddressUpdateRequest,
    ) -> Address | None:
        """
        Update an address for an account type info.

        Args:
            address_friendly_id (str): The friendly ID of the address to update
            account_type_info_id (GUID): The account type info ID
            address_request (AddressUpdateRequest): The address update request

        Returns:
            Address | None: The updated address or None if not found
        """
        try:
            address = await self.get_address_by_friendly_id(address_friendly_id, account_type_info_id)
            if not address:
                return None

            update_data = {}
            if address_request.phone_number is not None:
                update_data["phone_number"] = address_request.phone_number
            if address_request.address is not None:
                update_data["address"] = address_request.address
            if address_request.city is not None:
                update_data["city"] = address_request.city
            if address_request.state is not None:
                update_data["state"] = address_request.state
            if address_request.postal_code is not None:
                update_data["postal_code"] = address_request.postal_code
            if address_request.country_id is not None:
                update_data["country_id"] = address_request.country_id
            if address_request.is_default is not None:
                update_data["is_default"] = address_request.is_default

            address_update = AddressUpdate(**update_data)

            return await self.address_repository.update_address_for_entity(
                address_id=address.id,
                addressable_type="AccountTypeInfo",
                addressable_id=account_type_info_id,
                address_data=address_update,
            )
        except errors.DatabaseError as de:
            logger.error(
                f"DatabaseError updating address {address_friendly_id}: {de.detail}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to update address") from de
        except errors.ServiceError:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error updating address {address_friendly_id}: {str(e)}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to update address") from e

    async def delete_address_for_account_type_info(
        self,
        address_friendly_id: str,
        account_type_info_id: GUID,
    ) -> bool:
        """
        Delete an address for an account type info.

        Args:
            address_friendly_id (str): The friendly ID of the address to delete
            account_type_info_id (GUID): The account type info ID

        Returns:
            bool: True if the address was deleted, False if not found
        """
        try:
            address = await self.get_address_by_friendly_id(address_friendly_id, account_type_info_id)
            if not address:
                return False

            return await self.address_repository.delete_address_for_entity(
                address_id=address.id,
                addressable_type="AccountTypeInfo",
                addressable_id=account_type_info_id,
            )
        except errors.DatabaseError as de:
            logger.error(
                f"DatabaseError deleting address {address_friendly_id}: {de.detail}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to delete address") from de
        except Exception as e:
            logger.error(
                f"Unexpected error deleting address {address_friendly_id}: {str(e)}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to delete address") from e

    async def get_default_address_for_account_type_info(self, account_type_info_id: GUID) -> Address | None:
        """
        Get the default address for an account type info.

        Args:
            account_type_info_id (GUID): The account type info ID

        Returns:
            Address | None: The default address or None if not found
        """
        try:
            return await self.address_repository.get_default_address_for_entity(
                addressable_type="AccountTypeInfo", addressable_id=account_type_info_id
            )
        except errors.DatabaseError as de:
            logger.error(
                f"DatabaseError getting default address for account type info {account_type_info_id}: {de.detail}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to retrieve default address") from de
        except Exception as e:
            logger.error(
                f"Unexpected error getting default address for account type info {account_type_info_id}: {str(e)}",
                exc_info=True,
            )
            raise errors.ServiceError(detail="Failed to retrieve default address") from e
