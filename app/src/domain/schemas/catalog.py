from decimal import Decimal
from typing import Annotated, Optional
from uuid import UUID

from fastapi import File, UploadFile
from pydantic import BaseModel, BeforeValidator, Field
from src.core.helpers.request import parse_comma_separated_list
from src.core.types import GUID
from src.domain.enums import ProductStatus
from src.libs.query_engine import PaginationType


class CatalogFilterParams(BaseModel):
    """
    Filter parameters for catalog browsing.
    """

    status: Annotated[list[ProductStatus] | None, BeforeValidator(parse_comma_separated_list(ProductStatus))] = None
    category: Annotated[list[str] | None, BeforeValidator(parse_comma_separated_list)] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    search: Optional[str] = None


class CatalogBrowseParams(BaseModel):
    """
    Complete parameters for catalog browsing, including filters and pagination.
    """

    filters: Optional[CatalogFilterParams] = None
    include: Annotated[list[str] | None, BeforeValidator(parse_comma_separated_list)] = None
    fields: Optional[str] = None
    order_by: Annotated[list[str] | None, BeforeValidator(parse_comma_separated_list)] = None
    limit: int = Field(20, ge=1, le=100)
    cursor: Optional[str] = None
    offset: int = Field(0, ge=0)
    page: Optional[int] = Field(None, ge=1)
    pagination_type: PaginationType = PaginationType.KEYSET
    include_total_count: bool = False


DEFAULT_CATALOG_RETURN_FIELDS = [
    "id",
    "friendly_id",
    "name",
    "description",
    "price",
    "currency",
    "status",
    "currency_id",
    "category_id",
    "attributes",
    "is_digital",
    "created_datetime",
    "updated_datetime",
]


class CatalogItemCreateRequest(BaseModel):
    """
    Schema for creating a new catalog item
    """

    name: str = Field(..., description="The name of the product")
    description: str | None = Field(None, description="A description of the product")
    price: Decimal = Field(..., ge=0.01, decimal_places=2, description="The base price of the product as string")
    currency_id: UUID = Field(..., description="The currency ID as string")
    category_id: GUID = Field(..., description="The category ID as string")
    is_digital: bool = Field(False, description="Whether the product is a digital good")
    attributes: str | None = Field(None, description="JSON string of product attributes")
    initial_stock: int = Field(1, ge=1, description="Initial quantity in stock")
    attachments: list[UploadFile] = File(..., description="List of attachment files")
    attachment_names: list[str] = Field(..., description="Names for attachments")
