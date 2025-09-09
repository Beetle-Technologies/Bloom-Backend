from abc import ABC, abstractmethod
from typing import Any, Optional

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from .schemas import GeneralPaginationRequest, GeneralPaginationResponse


class QueryEngineInterface(ABC):
    """Abstract interface for query engine implementations"""

    def __init__(self, model: type[SQLModel], session: AsyncSession):
        self.model = model
        self.session = session

    @abstractmethod
    async def query(
        self,
        filters: Optional[dict[str, Any]] = None,
        fields: Optional[str] = "*",
        include: Optional[list[str]] = None,
        order_by: Optional[list[str]] = None,
    ) -> SQLModel:
        """
        Query for a single entity.

        Args:
            filters: Dictionary of filter conditions
            fields: Comma-separated string of fields to select or "*" for all fields
            include: List of relationships to include
            order_by: List of fields to order by

        Returns:
            Single entity

        Raises:
            EntityNotFoundError: When no entity is found
            MultipleEntitiesFoundError: When multiple entities are found
        """
        pass

    @abstractmethod
    async def paginate(
        self,
        pagination: GeneralPaginationRequest,
    ) -> GeneralPaginationResponse:
        """
        Paginate entities with filtering, ordering, and includes.

        Args:
            pagination: Pagination request parameters

        Returns:
            Paginated response without pagination_type in the data
        """
        pass
