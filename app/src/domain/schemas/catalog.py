from decimal import Decimal
from typing import Annotated, Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, Field
from src.core.helpers.request import parse_bool, parse_comma_separated_list
from src.core.types import GUID
from src.domain.enums import ProductStatus
from src.libs.query_engine import PaginationType


class CatalogFilterParams(BaseModel):
    """
    Filter parameters for catalog browsing.
    """

    status: Annotated[
        list[ProductStatus] | None,
        BeforeValidator(parse_comma_separated_list(ProductStatus)),
    ] = None
    category: Annotated[list[str] | list[GUID] | None, BeforeValidator(parse_comma_separated_list())] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    search: Optional[str] = None
    is_product: Annotated[bool, BeforeValidator(parse_bool())] = False


class CatalogBrowseParams(BaseModel):
    """
    Complete parameters for catalog browsing, including filters and pagination.
    """

    filters: Optional[CatalogFilterParams] = None
    include: Annotated[list[str] | None, BeforeValidator(parse_comma_separated_list())] = None
    fields: Optional[str] = None
    order_by: Annotated[list[str] | None, BeforeValidator(parse_comma_separated_list())] = None
    limit: int = Field(20, ge=1, le=100)
    cursor: Optional[str] = None
    offset: int = Field(0, ge=0)
    page: Optional[int] = Field(None, ge=1)
    pagination_type: PaginationType = PaginationType.KEYSET
    include_total_count: bool = False


class CatalogItemCreateRequest(BaseModel):
    """
    Schema for creating a new catalog item
    """

    id: GUID = Field(
        ...,
        description="The unique identifier for the product",
        examples=["gid://bloom/Product/dGVzdGluZ3Rlc3Rpbmc"],
    )
    name: str = Field(..., description="The name of the product")
    description: str | None = Field(None, description="A description of the product")
    price: Decimal = Field(
        ...,
        ge=0.01,
        decimal_places=2,
        description="The base price of the product as string",
    )
    currency_id: UUID = Field(..., description="The currency ID as string")
    category_id: GUID = Field(
        ...,
        description="The category ID as string",
        examples=["gid://bloom/Category/dGVzdGluZ3Rlc3Rpbmc"],
    )
    status: ProductStatus = Field(ProductStatus.ACTIVE, description="The status of the catalog item")
    is_digital: bool = Field(False, description="Whether the product is a digital good")
    attributes: dict[str, Any] = Field({}, description="JSON object of product attributes")
    initial_stock: int = Field(1, ge=1, description="Initial quantity in stock")


class AdjustInventoryRequest(BaseModel):
    """
    Schema for adjusting the inventory
    """

    quantity_change: int = Field(..., description="Quantity to add (positive) or remove (negative)")
    reason: str | None = Field(None, description="Reason for the adjustment")


class RequestItemRequest(BaseModel):
    """
    Schema for create product item for sale
    """

    requested_quantity: int | None = Field(None, gt=0, description="Quantity requested")
    mode: str = Field(default="implicit", description="Request mode: implicit or explicit")
    name: Optional[str] = Field(None, description="Name of the item")
    description: Optional[str] = Field(None, description="Description of the item")
    markup_percentage: Decimal = Field(
        ...,
        ge=5.00,
        decimal_places=2,
        description="Markup percentage over product price (for ProductItem)",
    )
    attributes: Optional[Dict[str, Any]] = Field(None, description="Attributes specific to this item")


class CatalogItemUpdateRequest(BaseModel):
    """
    Generalized schema for updating catalog items (Product or ProductItem).
    """

    name: Optional[str] = Field(None, description="Name of the item")
    description: Optional[str] = Field(None, description="Description of the item")
    price: Optional[Decimal] = Field(None, description="Price (for Product) or base price (for ProductItem)")
    markup_percentage: Optional[Decimal] = Field(None, description="Markup percentage (for ProductItem)")
    currency_id: Optional[UUID] = Field(None, description="Currency ID")
    category_id: Optional[GUID] = Field(None, description="Category ID")
    status: Optional[ProductStatus] = Field(None, description="Status")
    is_digital: Optional[bool] = Field(None, description="Whether it's digital")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Attributes for the item")
