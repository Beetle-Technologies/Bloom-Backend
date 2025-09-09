from sqlalchemy import func
from sqlmodel import SQLModel, col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..schemas import OffsetPaginationRequest, OffsetPaginationResponse, SortDirection


class OffsetProvider:
    """Provider for constructing offset/limit pagination queries"""

    def __init__(self, model: type[SQLModel], session: AsyncSession):
        self.model = model
        self.session = session

    async def paginate(
        self,
        query,
        pagination: OffsetPaginationRequest,
        total_count: int | None = None,
    ) -> OffsetPaginationResponse:
        """
        Handle offset pagination

        Args:
            query: The base query to paginate
            pagination: Pagination request parameters
            total_count: Optional pre-calculated total count

        Returns:
            OffsetPaginationResponse with paginated results
        """
        # Calculate pagination metadata
        offset = pagination.get_offset()
        page = pagination.get_page()

        # Get total count if not provided
        if total_count is None and pagination.include_total_count:
            total_count = await self._get_total_count(query)

        total_pages = (total_count + pagination.limit - 1) // pagination.limit if total_count and total_count > 0 else 1

        # Apply ordering
        sort_fields = pagination.get_sort_fields()
        ordered_query = self._apply_ordering(query, sort_fields)

        # Apply offset and limit
        paginated_query = ordered_query.offset(offset).limit(pagination.limit)

        # Execute query
        result = await self.session.exec(paginated_query)
        items = list(result.all())

        # Create response
        return OffsetPaginationResponse(
            items=items,
            total_count=total_count or 0,
            page=page,
            per_page=pagination.limit,
            total_pages=total_pages,
            has_next=page < total_pages if total_count else False,
            has_previous=page > 1,
        )

    def _apply_ordering(self, query, sort_fields: list[tuple[str, SortDirection]]):
        """Apply ordering to the query"""
        for field_name, direction in sort_fields:
            if hasattr(self.model, field_name):
                model_attr = getattr(self.model, field_name)
                if direction == SortDirection.ASC:
                    query = query.order_by(col(model_attr).asc())
                else:
                    query = query.order_by(col(model_attr).desc())
        return query

    async def _get_total_count(self, query) -> int:
        """Get total count of records for the given query"""
        # Create a count query from the base query
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.session.exec(count_query)
        return result.one()

    def _parse_sort_fields(self, order_by: list[str]) -> list[tuple[str, SortDirection]]:
        """Parse sort fields from order_by list"""
        fields = []
        for field in order_by:
            if field.startswith("-"):
                fields.append((field[1:], SortDirection.DESC))
            else:
                fields.append((field, SortDirection.ASC))
        return fields
