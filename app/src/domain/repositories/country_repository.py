from __future__ import annotations

import logging

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.domain.models.country import Country
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas import CountryCreate, CountryUpdate

logger = logging.getLogger(__name__)


class CountryRepository(BaseRepository[Country, CountryCreate, CountryUpdate]):
    """
    Repository for managing countries in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Country, session)

    async def find_by_name(self, name) -> Country | None:
        """
        Find a country by its name.

        Args:
            name: The country name to search for (CountryEnum)

        Returns:
            Country | None: The found country or None
        """
        return await self.find_one_by_and_none(name=name)

    async def find_active_countries(self) -> list[Country]:
        """
        Find all active countries.

        Returns:
            list[Country]: List of active countries
        """
        query = select(self.model).where(self.model.is_active == True)  # noqa: E712
        result = await self.session.exec(query)
        return list(result.all())

    async def find_by_currency_id(self, currency_id: str) -> list[Country]:
        """
        Find all countries using a specific currency.

        Args:
            currency_id (str): The currency ID to search for

        Returns:
            list[Country]: List of countries using the currency
        """
        query = select(self.model).where(self.model.currency_id == currency_id)
        result = await self.session.exec(query)
        return list(result.all())

    async def create_if_not_exists(self, schema: CountryCreate) -> Country:
        """
        Create a country if it doesn't already exist.

        Args:
            schema (CountryCreate): The country data

        Returns:
            Country: The existing or newly created country
        """
        existing = await self.find_by_name(schema.name)

        if existing:
            return existing

        return await self.create(schema)

    async def bulk_create_if_not_exists(self, schemas: list[CountryCreate]) -> list[Country]:
        """
        Bulk create countries if they don't already exist.

        Args:
            schemas (list[CountryCreate]): List of country data to create

        Returns:
            list[Country]: List of existing or newly created countries
        """
        results = []
        for schema in schemas:
            result = await self.create_if_not_exists(schema)
            results.append(result)
        return results
