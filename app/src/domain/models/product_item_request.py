from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import VARCHAR, Column, UniqueConstraint
from sqlmodel import Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID
from src.domain.enums import ProductItemRequestStatus

if TYPE_CHECKING:
    from src.domain.models import Account, Product


class ProductItemRequest(GUIDMixin, TimestampMixin, table=True):
    """
    Represents a request from a seller to sell a supplier's product.

    Attributes:
        id (GUID): The unique identifier for the request.
        requester_account_id (GUID): ID of the requesting seller account.
        supplier_account_id (GUID): ID of the supplier account.
        product_id (GUID): ID of the product to resell.
        requested_quantity (int): Quantity requested.
        status (str): Status ('pending', 'approved', 'rejected').
        created_datetime (datetime): When the request was made.
        updated_datetime (datetime | None): When the request was last updated.
    """

    __tablename__ = "product_item_requests"  # type: ignore

    __table_args__ = (
        UniqueConstraint(
            "seller_account_id",
            "supplier_account_id",
            "product_id",
            name="uq_resale_request__seller__supplier__product",
        ),
    )

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "requester_account_id",
        "supplier_account_id",
        "product_id",
        "requested_quantity",
        "status",
        "created_datetime",
        "updated_datetime",
    ]

    seller_account_id: GUID = Field(foreign_key="accounts.id", nullable=False, index=True)
    supplier_account_id: GUID = Field(foreign_key="accounts.id", nullable=False, index=True)
    mode: str = Field(max_length=50, nullable=False, index=True, default="implicit")  # implicit or explicit
    product_id: GUID = Field(foreign_key="products.id", nullable=False, index=True)
    requested_quantity: int = Field(nullable=False)
    status: ProductItemRequestStatus = Field(
        sa_column=Column(
            VARCHAR(50),
            nullable=False,
            default=ProductItemRequestStatus.PENDING,
        )
    )

    # Relationships
    seller: "Account" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[ProductItemRequest.seller_account_id]",
            "back_populates": "resale_requests_as_seller",
        }
    )
    supplier: "Account" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[ProductItemRequest.supplier_account_id]",
            "back_populates": "resale_requests_as_supplier",
        }
    )
    product: "Product" = Relationship(back_populates="resale_requests")
