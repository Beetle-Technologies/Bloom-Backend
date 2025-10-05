from typing import Any, Optional

from sqlalchemy.orm import selectinload
from sqlmodel import SQLModel, col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .interface import QueryEngineInterface
from .providers.filters import FiltersProvider
from .providers.keyset import KeysetProvider
from .providers.offset import OffsetProvider
from .providers.selection import SelectionProvider
from .schemas import (
    GeneralPaginationRequest,
    GeneralPaginationResponse,
    KeysetCursor,
    KeysetPaginationRequest,
    KeysetPaginationResponse,
    OffsetPaginationRequest,
    OffsetPaginationResponse,
    PaginationType,
    SortDirection,
)


class QueryEngineService(QueryEngineInterface):
    """
    General query engine that supports field selection, filters, includes, keyset and offset pagination.
    """

    def __init__(self, model: type[SQLModel], session: AsyncSession):
        super().__init__(model, session)
        self.keyset_provider = KeysetProvider(model)
        self.filter_provider = FiltersProvider(model)
        self.selection_provider = SelectionProvider(model)
        self.offset_provider = OffsetProvider(model, session)

    async def query(
        self,
        filters: Optional[dict[str, Any]] = None,
        fields: Optional[str] = "*",
        include: Optional[list[str]] = None,
        order_by: Optional[list[str]] = None,
    ) -> Any:
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
            InvalidFieldError: When invalid fields are specified
        """
        # Validate select fields
        if fields:
            self.selection_provider.validate_fields(fields)

        # Build base query with field selection
        query = self.selection_provider.build_select_query(fields)

        # Apply joins, includes, filters, and ordering
        query = self._build_complete_query(query, filters, include, order_by)

        # Execute query
        result = await self.session.exec(query)
        item = result.one_or_none()

        return item

    async def query_all(
        self,
        filters: Optional[dict[str, Any]] = None,
        fields: Optional[str] = "*",
        include: Optional[list[str]] = None,
        order_by: Optional[list[str]] = None,
    ) -> list[Any]:
        """
        Query for all entities matching the criteria.

        Args:
            filters: Dictionary of filter conditions
            fields: Comma-separated string of fields to select or "*" for all fields
            include: List of relationships to include
            order_by: List of fields to order by

        Returns:
            List of entities
        """
        # Validate select fields
        if fields:
            self.selection_provider.validate_fields(fields)

        # Build base query with field selection
        query = self.selection_provider.build_select_query(fields)

        # Apply joins, includes, filters, and ordering
        query = self._build_complete_query(query, filters, include, order_by)

        # Execute query
        result = await self.session.exec(query)
        items = result.all()

        return list(items)

    async def paginate(
        self,
        pagination: GeneralPaginationRequest,
    ) -> GeneralPaginationResponse:
        """
        Paginate results using the specified pagination type.

        Args:
            pagination: General pagination request

        Returns:
            Pagination response (keyset or offset based on type)
        """
        # Validate select fields
        if pagination.fields:
            self.selection_provider.validate_fields(pagination.fields)

        if pagination.pagination_type == PaginationType.KEYSET:
            response = await self._paginate_keyset(pagination.to_keyset_request())
        else:
            response = await self._paginate_offset(pagination.to_offset_request())

        # Convert to GeneralPaginationResponse to ensure consistent format
        return GeneralPaginationResponse.from_existing_response(response)

    async def _paginate_keyset(
        self,
        pagination: KeysetPaginationRequest,
    ) -> KeysetPaginationResponse:
        """Handle keyset pagination"""
        # Parse sort fields and ensure uniqueness
        sort_fields = self.keyset_provider.ensure_unique_sort(pagination.get_sort_fields())

        # Build base query with field selection
        query = self.selection_provider.build_select_query(pagination.fields)

        # Apply joins, includes, and filters
        query = self._build_complete_query(query, pagination.filters, pagination.include)

        # Apply cursor-based WHERE clause if cursor is provided
        if pagination.cursor:
            try:
                cursor = KeysetCursor.from_base64(pagination.cursor)
                where_clause = self.keyset_provider.build_where_clause(cursor)
                if where_clause is not None:
                    query = query.where(where_clause)
            except ValueError:
                # Invalid cursor, ignore it and start from beginning
                pass

        # Apply ordering
        order_clauses = self.keyset_provider.build_order_clause(sort_fields)
        for order_clause in order_clauses:
            query = query.order_by(order_clause)

        # Fetch one extra item to check if there are more pages
        query = query.limit(pagination.limit + 1)

        # Execute query
        result = await self.session.exec(query)
        items = list(result.all())

        # Check if there are more items
        has_next = len(items) > pagination.limit
        if has_next:
            items = items[:-1]  # Remove the extra item

        # Create response
        response = KeysetPaginationResponse(
            items=items,
            has_next=has_next,
            has_previous=pagination.cursor is not None,
        )

        # Generate next cursor if there are more items
        if has_next and items:
            last_item = items[-1]
            next_cursor = self.keyset_provider.create_cursor_from_row(last_item, sort_fields)
            response.next_cursor = next_cursor.to_base64()

        # Generate previous cursor if this isn't the first page
        if pagination.cursor is not None and items:
            first_item = items[0]
            # For previous cursor, we need to reverse the sort direction
            reverse_sort_fields = [
                (
                    name,
                    (SortDirection.DESC if direction == SortDirection.ASC else SortDirection.ASC),
                )
                for name, direction in sort_fields
            ]
            previous_cursor = self.keyset_provider.create_cursor_from_row(first_item, reverse_sort_fields)
            response.previous_cursor = previous_cursor.to_base64()

        # Include total count if requested (this can be expensive)
        if pagination.include_total_count:
            response.total_count = await self._get_total_count(pagination.filters, pagination.include)

        return response

    async def _paginate_offset(
        self,
        pagination: OffsetPaginationRequest,
    ) -> OffsetPaginationResponse:
        """Handle offset pagination"""
        # Build base query with field selection
        query = self.selection_provider.build_select_query(pagination.fields)

        # Apply joins, includes, and filters
        query = self._build_complete_query(query, pagination.filters, pagination.include)

        # Get total count if requested
        total_count = None
        if pagination.include_total_count:
            total_count = await self._get_total_count(pagination.filters, pagination.include)

        # Use the offset provider to handle pagination
        return await self.offset_provider.paginate(query, pagination, total_count)

    def _build_complete_query(
        self,
        query,
        filters: Optional[dict[str, Any]] = None,
        include: Optional[list[str]] = None,
        order_by: Optional[list[str]] = None,
    ):
        """Build a complete query with joins, includes, filters, and ordering"""
        # Apply joins for relationship filters
        if filters:
            query = self._apply_joins(query, filters)

        # Apply includes (selectinload)
        if include:
            query = self._apply_includes(query, include)

        # Apply filters
        if filters:
            query = self._apply_filters(query, filters)

        # Apply ordering
        if order_by:
            sort_fields = self._parse_sort_fields(order_by)
            for field_name, direction in sort_fields:
                if hasattr(self.model, field_name):
                    field_attr = getattr(self.model, field_name)
                    if direction == SortDirection.ASC:
                        query = query.order_by(col(field_attr).asc())
                    else:
                        query = query.order_by(col(field_attr).desc())

        return query

    def _apply_joins(self, query, filters: dict[str, Any]):
        """Apply necessary joins for relationship filters"""
        required_joins = self.filter_provider.get_required_joins(filters)

        for join_relationship in required_joins:
            if hasattr(self.model, join_relationship):
                relationship = getattr(self.model, join_relationship)
                query = query.join(relationship)

        return query

    def _apply_includes(self, query, includes: list[str]):
        """Apply selectinload for relationships, supporting nested paths."""
        for include in includes:
            if "." in include:
                parts = include.split(".")
                current_class = self.model
                loader = None

                for part in parts:
                    attr = getattr(current_class, part)
                    if loader is None:
                        loader = selectinload(attr)
                    else:
                        loader = loader.selectinload(attr)

                    if hasattr(attr, "property") and hasattr(attr.property, "mapper"):
                        current_class = attr.property.mapper.class_

                if loader:
                    query = query.options(loader)
            else:
                if hasattr(self.model, include):
                    relationship = getattr(self.model, include)
                    query = query.options(selectinload(relationship))

        return query

    def _apply_filters(self, query, filters: dict[str, Any]):
        """Apply filters to the query with support for complex logical operators"""
        filter_conditions = self.filter_provider.build_filter_conditions(filters)
        if filter_conditions is not None:
            query = query.where(filter_conditions)

        return query

    async def _get_total_count(
        self,
        filters: Optional[dict[str, Any]] = None,
        include: Optional[list[str]] = None,
    ) -> int:
        """Get total count of records matching the filters"""
        from sqlalchemy import func

        query = select(func.count()).select_from(self.model)

        # Apply joins for relationship filters
        if filters:
            query = self._apply_joins(query, filters)

        # Apply filters
        if filters:
            filter_conditions = self.filter_provider.build_filter_conditions(filters)
            if filter_conditions is not None:
                query = query.where(filter_conditions)

        result = await self.session.exec(query)
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
