from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.models.address import Address
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas import AddressCreate, AddressUpdate
from src.libs.query_engine.exceptions import QueryEngineError
from src.libs.query_engine.schemas import BaseQueryEngineParams

logger = get_logger(__name__)


class AddressRepository(BaseRepository[Address, AddressCreate, AddressUpdate]):
    """
    Repository for managing addresses in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Address, session)

    async def get_by_friendly_id(self, friendly_id: str) -> Address | None:
        """Get address by friendly ID."""
        try:
            statement = select(Address).where(Address.friendly_id == friendly_id)
            result = await self.session.exec(statement)
            return result.first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting address by friendly_id {friendly_id}: {str(e)}")
            raise errors.DatabaseError(detail="Failed to retrieve address") from e

    async def get_addresses_for_entity(self, addressable_type: str, addressable_id: GUID) -> Sequence[Address]:
        """
        Get all addresses for a specific entity.

        Args:
            addressable_type (str): The type of entity (e.g., 'AccountTypeInfo')
            addressable_id (GUID): The ID of the entity

        Returns:
            Sequence[Address]: List of addresses for the entity
        """
        try:
            statement = (
                select(Address)
                .where(
                    Address.addressable_type == addressable_type,
                    Address.addressable_id == addressable_id,
                )
                .order_by(col(Address.is_default).desc(), col(Address.created_datetime).desc())
            )
            result = await self.session.exec(statement)
            return result.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting addresses for {addressable_type} {addressable_id}: {str(e)}")
            raise errors.DatabaseError(detail="Failed to retrieve addresses") from e

    async def get_default_address_for_entity(self, addressable_type: str, addressable_id: GUID) -> Address | None:
        """
        Get the default address for a specific entity.

        Args:
            addressable_type (str): The type of entity
            addressable_id (GUID): The ID of the entity

        Returns:
            Address | None: The default address or None if not found
        """
        try:
            result = await self.query(
                params=BaseQueryEngineParams(
                    filters={
                        "addressable_type": addressable_type,
                        "addressable_id": addressable_id,
                        "is_default": True,
                    }
                )
            )
            return result
        except SQLAlchemyError as e:
            logger.error(f"Error getting default address for {addressable_type} {addressable_id}: {str(e)}")
            raise errors.DatabaseError(detail="Failed to retrieve default address") from e
        except QueryEngineError as qe:
            logger.error(f"Query engine error: {str(qe)}")
            raise errors.DatabaseError(detail="Failed to retrieve default address") from qe

    async def clear_default_addresses_for_entity(self, addressable_type: str, addressable_id: GUID) -> None:
        """
        Clear all default address flags for a specific entity.
        This is useful when setting a new default address.

        Args:
            addressable_type (str): The type of entity
            addressable_id (GUID): The ID of the entity
        """
        try:
            addresses = await self.get_addresses_for_entity(addressable_type, addressable_id)
            for address in addresses:
                if address.is_default:
                    await self.update(address.id, {"is_default": False})
        except SQLAlchemyError as e:
            logger.error(f"Error clearing default addresses for {addressable_type} {addressable_id}: {str(e)}")
            raise errors.DatabaseError(detail="Failed to clear default addresses") from e

    async def create_address_for_entity(
        self,
        addressable_type: str,
        addressable_id: GUID,
        address_data: AddressCreate,
    ) -> Address:
        """
        Create an address for a specific entity.

        Args:
            addressable_type (str): The type of entity
            addressable_id (GUID): The ID of the entity
            address_data (AddressCreate): The address data

        Returns:
            Address: The created address
        """
        try:
            if address_data.is_default:
                await self.clear_default_addresses_for_entity(addressable_type, addressable_id)

            full_address_data = AddressCreate(
                addressable_type=addressable_type,
                addressable_id=addressable_id,
                **address_data.model_dump(),
            )

            return await self.create(full_address_data)
        except SQLAlchemyError as e:
            logger.error(f"Error creating address for {addressable_type} {addressable_id}: {str(e)}")
            raise errors.DatabaseError(detail="Failed to create address") from e

    async def update_address_for_entity(
        self,
        address_id: GUID,
        addressable_type: str,
        addressable_id: GUID,
        address_data: AddressUpdate,
    ) -> Address | None:
        """
        Update an address for a specific entity.

        Args:
            address_id (GUID): The ID of the address to update
            addressable_type (str): The type of entity (for validation)
            addressable_id (GUID): The ID of the entity (for validation)
            address_data (AddressUpdate): The updated address data

        Returns:
            Address | None: The updated address or None if not found
        """
        try:
            existing_address = await self.find_one_by_or_none(
                id=address_id,
                addressable_type=addressable_type,
                addressable_id=addressable_id,
            )

            if not existing_address:
                return None

            if address_data.is_default:  # type: ignore
                await self.clear_default_addresses_for_entity(addressable_type, addressable_id)

            return await self.update(address_id, address_data)
        except SQLAlchemyError as e:
            logger.error(f"Error updating address {address_id}: {str(e)}")
            raise errors.DatabaseError(detail="Failed to update address") from e

    async def delete_address_for_entity(
        self,
        address_id: GUID,
        addressable_type: str,
        addressable_id: GUID,
    ) -> bool:
        """
        Delete an address for a specific entity.

        Args:
            address_id (GUID): The ID of the address to delete
            addressable_type (str): The type of entity (for validation)
            addressable_id (GUID): The ID of the entity (for validation)

        Returns:
            bool: True if the address was deleted, False if not found
        """
        try:
            existing_address = await self.find_one_by_or_none(
                id=address_id,
                addressable_type=addressable_type,
                addressable_id=addressable_id,
            )

            if not existing_address:
                return False

            await self.session.delete(existing_address)
            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting address {address_id}: {str(e)}")
            raise errors.DatabaseError(detail="Failed to delete address") from e
