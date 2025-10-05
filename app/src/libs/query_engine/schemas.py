from typing import Any, Generic, TypeVar, Union
from uuid import UUID

from pydantic import BaseModel, Field

from .enums import PaginationType, SortDirection


class BaseQueryEngineParams(BaseModel):
    """
    Parameters for the query engine

    Attributes:
        filters (dict[str, Any]): Filters to apply to the query.
        include (list[str] | None): Related fields to include in the query.
        fields (str | None): Specific fields to return in the query.
    """

    filters: dict[str, Any] = Field(default_factory=dict)
    include: list[str] | None = Field(default_factory=list)
    fields: str | None = Field(default="*")
    order_by: list[str] | None = Field(default_factory=list)


class KeysetField(BaseModel):
    """
    Represents a field used in keyset pagination

    Attributes:\n
        name (str): The name of the field.
        value (Any): The value of the field, can be any type.
        direction (SortDirection): The sort direction for this field, defaults to ascending.
    """

    name: str
    value: Any
    direction: SortDirection = SortDirection.ASC


class KeysetCursor(BaseModel):
    """
    Represents a keyset cursor for pagination

    Attributes:\n
        fields (list[KeysetField]): List of fields that define the cursor.
    """

    fields: list[KeysetField]

    def to_base64(self) -> str:
        """Encode cursor to base64 string"""
        import base64
        import json

        # Convert to dict for JSON serialization
        cursor_dict = {
            "fields": [
                {
                    "name": field.name,
                    "value": (str(field.value) if isinstance(field.value, UUID) else field.value),
                    "direction": field.direction.value,
                }
                for field in self.fields
            ]
        }

        json_str = json.dumps(cursor_dict, default=str, sort_keys=True)
        return base64.b64encode(json_str.encode()).decode()

    @classmethod
    def from_base64(cls, cursor_str: str) -> "KeysetCursor":
        """Decode cursor from base64 string"""
        import base64
        import json
        from datetime import datetime
        from uuid import UUID

        try:
            json_str = base64.b64decode(cursor_str.encode()).decode()
            cursor_dict = json.loads(json_str)

            fields = []
            for field_data in cursor_dict["fields"]:
                value = field_data["value"]

                # Try to convert back to proper types
                if isinstance(value, str):
                    # Try UUID first
                    try:
                        value = UUID(value)
                    except ValueError:
                        # Try datetime
                        try:
                            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                        except ValueError:
                            # Keep as string
                            pass

                fields.append(
                    KeysetField(
                        name=field_data["name"],
                        value=value,
                        direction=SortDirection(field_data["direction"]),
                    )
                )

            return cls(fields=fields)
        except Exception as e:
            raise ValueError(f"Invalid cursor format: {e}")


class BasePaginationRequest(BaseModel):
    """Base class for pagination requests"""

    limit: int = Field(default=20, ge=1, le=100, description="Number of items to return")
    order_by: list[str] = Field(
        default_factory=lambda: ["created_datetime"],
        description="Fields to order by (prefix with - for DESC)",
    )
    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of column names and values to filter by",
    )
    include: list[str] = Field(
        default_factory=list,
        description="List of relationships to include (selectinload)",
    )
    include_total_count: bool = Field(
        default=False,
        description="Whether to include total count in response (can be expensive)",
    )
    fields: str = Field(
        default="*",
        description="Comma-separated list of fields to select, or '*' for all fields",
    )


class KeysetPaginationRequest(BasePaginationRequest):
    """Request parameters for keyset pagination"""

    cursor: str | None = Field(default=None, description="Base64 encoded cursor for pagination")

    def get_sort_fields(self) -> list[tuple[str, SortDirection]]:
        """Extract sort fields and directions from order_by"""
        fields = []
        for field in self.order_by:
            if field.startswith("-"):
                fields.append((field[1:], SortDirection.DESC))
            else:
                fields.append((field, SortDirection.ASC))
        return fields


class OffsetPaginationRequest(BasePaginationRequest):
    """Request parameters for offset/limit pagination"""

    offset: int = Field(default=0, ge=0, description="Number of items to skip")
    page: int | None = Field(default=None, ge=1, description="Page number (alternative to offset)")

    def get_offset(self) -> int:
        """Calculate offset from page number if provided"""
        if self.page is not None:
            return (self.page - 1) * self.limit
        return self.offset

    def get_page(self) -> int:
        """Calculate page number from offset"""
        if self.page is not None:
            return self.page
        return (self.offset // self.limit) + 1

    def get_sort_fields(self) -> list[tuple[str, SortDirection]]:
        """Extract sort fields and directions from order_by"""
        fields = []
        for field in self.order_by:
            if field.startswith("-"):
                fields.append((field[1:], SortDirection.DESC))
            else:
                fields.append((field, SortDirection.ASC))
        return fields


class GeneralPaginationRequest(BasePaginationRequest):
    """General pagination request that can handle both types"""

    pagination_type: PaginationType = Field(default=PaginationType.KEYSET, description="Type of pagination to use")
    # Keyset pagination fields
    cursor: str | None = Field(default=None, description="Base64 encoded cursor for keyset pagination")

    # Offset pagination fields
    offset: int = Field(default=0, ge=0, description="Number of items to skip for offset pagination")
    page: int | None = Field(default=None, ge=1, description="Page number for offset pagination")

    def to_keyset_request(self) -> KeysetPaginationRequest:
        """Convert to keyset pagination request"""
        return KeysetPaginationRequest(
            limit=self.limit,
            cursor=self.cursor,
            order_by=self.order_by,
            filters=self.filters,
            include=self.include,
            include_total_count=self.include_total_count,
            fields=self.fields,
        )

    def to_offset_request(self) -> OffsetPaginationRequest:
        """Convert to offset pagination request"""
        return OffsetPaginationRequest(
            limit=self.limit,
            offset=self.offset,
            page=self.page,
            order_by=self.order_by,
            filters=self.filters,
            include=self.include,
            include_total_count=self.include_total_count,
            fields=self.fields,
        )

    def get_sort_fields(self) -> list[tuple[str, SortDirection]]:
        """Extract sort fields and directions from order_by"""
        fields = []
        for field in self.order_by:
            if field.startswith("-"):
                fields.append((field[1:], SortDirection.DESC))
            else:
                fields.append((field, SortDirection.ASC))
        return fields


T = TypeVar("T")


class KeysetPaginationResponse(BaseModel, Generic[T]):
    """Response for keyset pagination"""

    items: list[T]
    has_next: bool = False
    has_previous: bool = False
    next_cursor: str | None = None
    previous_cursor: str | None = None
    total_count: int | None = None
    limit: int | None = None
    pagination_type: PaginationType = PaginationType.KEYSET

    class Config:
        arbitrary_types_allowed = True


class OffsetPaginationResponse(BaseModel, Generic[T]):
    """Response for offset pagination"""

    items: list[T]
    total_count: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_previous: bool
    pagination_type: PaginationType = PaginationType.OFFSET

    class Config:
        arbitrary_types_allowed = True


class GeneralPaginationResponse(BaseModel, Generic[T]):
    """
    General pagination response that can handle both offset and keyset pagination
    """

    items: list[T]
    has_next: bool = False
    has_previous: bool = False
    pagination_type: PaginationType

    # Offset pagination fields (optional)
    page: int | None = None
    per_page: int | None = None
    total_pages: int | None = None
    total_count: int | None = None

    # Keyset pagination fields (optional)
    next_cursor: str | None = None
    previous_cursor: str | None = None
    limit: int | None = None

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_offset_pagination(
        cls,
        items: list[T],
        page: int,
        per_page: int,
        total_count: int,
        total_pages: int,
        has_next: bool,
        has_previous: bool,
    ) -> "GeneralPaginationResponse[T]":
        """Create from offset pagination data"""
        return cls(
            items=items,
            has_next=has_next,
            has_previous=has_previous,
            pagination_type=PaginationType.OFFSET,
            page=page,
            per_page=per_page,
            total_count=total_count,
            total_pages=total_pages,
        )

    @classmethod
    def from_keyset_pagination(
        cls,
        items: list[T],
        has_next: bool,
        has_previous: bool,
        next_cursor: str | None = None,
        previous_cursor: str | None = None,
        limit: int | None = None,
        total_count: int | None = None,
    ) -> "GeneralPaginationResponse[T]":
        """Create from keyset pagination data"""
        return cls(
            items=items,
            has_next=has_next,
            has_previous=has_previous,
            pagination_type=PaginationType.KEYSET,
            next_cursor=next_cursor,
            previous_cursor=previous_cursor,
            limit=limit,
            total_count=total_count,
        )

    @classmethod
    def from_existing_response(
        cls,
        response: Union["OffsetPaginationResponse[T]", "KeysetPaginationResponse[T]"],
    ) -> "GeneralPaginationResponse[T]":
        """Convert existing pagination response to general format"""
        if isinstance(response, OffsetPaginationResponse):
            return cls.from_offset_pagination(
                items=response.items,
                page=response.page,
                per_page=response.per_page,
                total_count=response.total_count,
                total_pages=response.total_pages,
                has_next=response.has_next,
                has_previous=response.has_previous,
            )
        elif isinstance(response, KeysetPaginationResponse):
            return cls.from_keyset_pagination(
                items=response.items,
                has_next=response.has_next,
                has_previous=response.has_previous,
                next_cursor=response.next_cursor,
                previous_cursor=response.previous_cursor,
                limit=getattr(response, "limit", None),
                total_count=response.total_count,
            )
        else:
            raise ValueError(f"Unsupported pagination response type: {type(response)}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for frontend (without pagination_type)"""
        base_data = {
            "has_next": self.has_next,
            "has_previous": self.has_previous,
            "items": [
                item._asdict() if hasattr(item, "_asdict") else item.__dict__ for item in self.items  # type: ignore
            ],
        }

        if self.pagination_type == PaginationType.OFFSET:
            base_data.update(
                {
                    "page": self.page,
                    "per_page": self.per_page,
                    "total_pages": self.total_pages,
                    "total_count": self.total_count,
                }
            )
        elif self.pagination_type == PaginationType.KEYSET:
            base_data.update(
                {
                    "next_cursor": self.next_cursor,
                    "previous_cursor": self.previous_cursor,
                    "limit": self.limit,
                    "total_count": self.total_count,
                }
            )

        # Remove None values for cleaner response
        return {k: v for k, v in base_data.items() if v is not None}
