from typing import TYPE_CHECKING, ClassVar, Union

from sqlalchemy import CheckConstraint, Column, String, UniqueConstraint
from sqlmodel import Field, Relationship, select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID
from src.domain.enums import InventoriableType

if TYPE_CHECKING:
    from src.domain.models import InventoryAction, Product, ProductItem


class Inventory(GUIDMixin, TimestampMixin, table=True):
    """
    Represents inventory stock for a product or resale item owned or managed by an account.

    Attributes:
        id (GUID): The unique identifier for the inventory entry.
        inventoriable_type (str): Type of item being inventoried ('product' or 'resale').
        inventoriable_id (GUID): Reference to the product or resale item.
        quantity_in_stock (int): The total quantity in stock.
        reserved_stock (int): The quantity reserved for pending orders.
        available_stock (int): Computed field: quantity_in_stock - reserved_stock.
        created_datetime (datetime): The timestamp when the inventory was created.
        updated_datetime (datetime | None): The timestamp when the inventory was last updated.
    """

    __tablename__ = "inventory"  # type: ignore

    __table_args__ = (
        UniqueConstraint(
            "inventoriable_type",
            "inventoriable_id",
            name="uq_inventory_item",
        ),
        CheckConstraint("quantity_in_stock >= 0", name="chk_quantity_in_stock_positive"),
        CheckConstraint("reserved_stock >= 0", name="chk_reserved_stock_positive"),
        CheckConstraint("reserved_stock <= quantity_in_stock", name="chk_reserved_not_exceed_stock"),
    )

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "inventoriable_type",
        "inventoriable_id",
        "quantity_in_stock",
        "reserved_stock",
        "available_stock",
        "created_datetime",
        "updated_datetime",
    ]

    inventoriable_type: str = Field(
        sa_column=Column(String(50), nullable=False, index=True),
        description="Type of item being inventoried (product or resale)",
    )
    inventoriable_id: GUID = Field(nullable=False, index=True)
    quantity_in_stock: int = Field(default=0, nullable=False)
    reserved_stock: int = Field(default=0, nullable=False)

    @property
    def available_stock(self) -> int:
        """Calculate available stock as quantity_in_stock - reserved_stock."""
        return self.quantity_in_stock - self.reserved_stock

    # Relationships
    actions: list["InventoryAction"] = Relationship(
        back_populates="inventory", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    async def get_inventoriable_item(self, session: AsyncSession) -> Union["Product", "ProductItem"]:
        """
        Get the actual inventoriable item (Product or Resale) from the database.

        Args:
            session: AsyncSession to use for database queries

        Returns:
            The Product or Resale instance

        Raises:
            ValueError: If inventoriable_type is not recognized
            EntityNotFoundError: If the referenced item is not found
        """
        if self.inventoriable_type == InventoriableType.PRODUCT:
            from src.domain.models import Product

            query = select(Product).where(Product.id == self.inventoriable_id)
            result = await session.exec(query)
            item = result.one_or_none()

            if item is None:
                raise ValueError("Product was not found")
            return item

        elif self.inventoriable_type == InventoriableType.PRODUCT_ITEM:
            from src.domain.models import ProductItem

            query = select(ProductItem).where(ProductItem.id == self.inventoriable_id)
            result = await session.exec(query)
            item = result.one_or_none()

            if item is None:
                raise ValueError("Product item was not found")
            return item

        else:
            raise ValueError(f"Unknown inventoriable_type: {self.inventoriable_type}")

    def get_inventoriable_model_class(self) -> type[Union["Product", "ProductItem"]]:
        """
        Get the model class for the inventoriable item without database access.

        Returns:
            The Product or Resale model class

        Raises:
            ValueError: If inventoriable_type is not recognized
        """
        if self.inventoriable_type == InventoriableType.PRODUCT:
            from src.domain.models import Product

            return Product
        elif self.inventoriable_type == InventoriableType.PRODUCT_ITEM:
            from src.domain.models import ProductItem

            return ProductItem
        else:
            raise ValueError(f"Unknown inventoriable_type: {self.inventoriable_type}")

    @classmethod
    async def find_by_item(
        cls,
        session: AsyncSession,
        inventoriable_type: str,
        inventoriable_id: GUID,
        account_id: GUID | None = None,
    ) -> list["Inventory"]:
        """
        Find inventory records for a specific item.

        Args:
            session: AsyncSession to use for database queries
            inventoriable_type: Type of inventoriable item
            inventoriable_id: ID of the inventoriable item
            account_id: Optional account ID to filter by

        Returns:
            List of matching inventory records
        """
        query = select(Inventory).where(
            Inventory.inventoriable_type == inventoriable_type,
            Inventory.inventoriable_id == inventoriable_id,
        )

        result = await session.exec(query)
        return list(result.all())

    def can_reserve(self, quantity: int) -> bool:
        """
        Check if the requested quantity can be reserved from available stock.

        Args:
            quantity: Quantity to reserve

        Returns:
            True if quantity can be reserved, False otherwise
        """
        return self.available_stock >= quantity

    def is_in_stock(self) -> bool:
        """
        Check if there is any available stock.

        Returns:
            True if available_stock > 0, False otherwise
        """
        return self.available_stock > 0
