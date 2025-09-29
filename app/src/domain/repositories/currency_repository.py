from __future__ import annotations

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.logging import get_logger
from src.domain.models.currency import Currency
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas import CurrencyCreate, CurrencyUpdate

logger = get_logger(__name__)


class CurrencyRepository(BaseRepository[Currency, CurrencyCreate, CurrencyUpdate]):
    """
    Repository for managing currencies in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Currency, session)

    async def find_by_code(self, code) -> Currency | None:
        """
        Find a currency by its ISO 4217 code.

        Args:
            code: The currency code to search for (CurrencyCode enum or string)

        Returns:
            Currency | None: The found currency or None
        """
        return await self.find_one_by_and_none(code=code)

    async def find_active_currencies(self) -> list[Currency]:
        """
        Find all active currencies.

        Returns:
            list[Currency]: List of active currencies
        """
        query = select(self.model).where(self.model.is_active == True)  # noqa: E712
        result = await self.session.exec(query)
        return list(result.all())

    async def find_default_currency(self) -> Currency | None:
        """
        Find the default currency for the system.

        Returns:
            Currency | None: The default currency or None if not set
        """
        return await self.find_one_by_and_none(is_default=True)

    async def create_if_not_exists(self, schema: CurrencyCreate) -> Currency:
        """
        Create a currency if it doesn't already exist.

        Args:
            schema (CurrencyCreate): The currency data

        Returns:
            Currency: The existing or newly created currency
        """
        existing = await self.find_by_code(schema.code)

        if existing:
            return existing

        return await self.create(schema)

    async def bulk_create_if_not_exists(self, schemas: list[CurrencyCreate]) -> list[Currency]:
        """
        Bulk create currencies if they don't already exist.

        Args:
            schemas (list[CurrencyCreate]): List of currency data to create

        Returns:
            list[Currency]: List of existing or newly created currencies
        """
        results = []
        for schema in schemas:
            result = await self.create_if_not_exists(schema)
            results.append(result)
        return results

    async def set_as_default(self, currency_id) -> None:
        """
        Set a currency as the default currency and unset others.

        Args:
            currency_id: The ID of the currency to set as default
        """
        # First, unset all currencies as default
        query = select(self.model)
        result = await self.session.exec(query)
        currencies = result.all()

        for currency in currencies:
            currency.is_default = currency.id == currency_id

        await self.session.commit()
