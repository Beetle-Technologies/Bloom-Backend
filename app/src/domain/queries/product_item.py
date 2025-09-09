from typing import Any, Dict, Optional

from sqlmodel import and_, col, select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.types import GUID
from src.domain.models.product import Product
from src.domain.models.product_item import ProductItem


class ProductItemQueries:
    """Query helpers for ProductItem operations."""

    @staticmethod
    def get_effective_values_query(product_item_id: GUID):
        """
        Get a query that returns the effective values for a ProductItem.
        """
        return (
            select(ProductItem, Product)
            .join(Product, col(ProductItem.product_id) == Product.id)
            .where(col(ProductItem.id) == product_item_id)
        )

    @staticmethod
    def get_items_by_seller_query(seller_account_id: GUID):
        """Get all product items for a specific seller."""
        return select(ProductItem).where(
            col(ProductItem.seller_account_id) == seller_account_id
        )

    @staticmethod
    def get_items_by_product_query(product_id: GUID):
        """Get all product items based on a specific product."""
        return select(ProductItem).where(col(ProductItem.product_id) == product_id)

    @staticmethod
    def get_items_with_custom_values_query():
        """Get product items that have any custom (non-null) values."""
        return select(ProductItem).where(
            and_(
                col(ProductItem.name).is_not(None),
                col(ProductItem.description).is_not(None),
                col(ProductItem.price).is_not(None),
                col(ProductItem.currency_id).is_not(None),
                col(ProductItem.category_id).is_not(None),
                col(ProductItem.status).is_not(None),
                col(ProductItem.is_digital).is_not(None),
                col(ProductItem.attributes).is_not(None),
            )
        )

    @staticmethod
    async def get_computed_price(
        session: AsyncSession, product_id: GUID, markup_percentage: float
    ) -> Optional[float]:
        """
        Calculate what the price would be for a given product and markup.
        Useful for previewing prices before creating a ProductItem.
        """
        result = await session.exec(
            select("products.price").where(Product.id == product_id)
        )
        product_price = result.first()

        if product_price is None:
            return None

        return float(product_price) * (1 + markup_percentage / 100)

    @staticmethod
    async def validate_price_constraint(
        session: AsyncSession, product_id: GUID, item_price: float
    ) -> bool:
        """
        Validate that the product item price is different from the product price.
        Returns True if valid (prices are different), False if invalid (prices are same).
        """
        result = await session.exec(
            select("products.price").where(Product.id == product_id)
        )
        product_price = result.first()

        if product_price is None:
            return False

        return float(product_price) != item_price

    @staticmethod
    def get_items_with_markup_range_query(min_markup: float, max_markup: float):
        """Get product items within a specific markup percentage range."""
        return select(ProductItem).where(
            and_(
                col(ProductItem.markup_percentage) >= min_markup,
                col(ProductItem.markup_percentage) <= max_markup,
            )
        )


async def create_product_item_with_defaults(
    session: AsyncSession,
    product_id: GUID,
    seller_account_id: GUID,
    markup_percentage: float = 0.0,
    **custom_overrides: Any
) -> ProductItem:
    """
    Create a ProductItem with automatic field population via triggers.

    Args:
        session: Database session
        product_id: ID of the product to base this item on
        seller_account_id: ID of the seller account
        markup_percentage: Markup percentage to apply
        **custom_overrides: Any fields to override (name, description, price, etc.)

    Returns:
        The created ProductItem instance
    """
    item_data = {
        "product_id": product_id,
        "seller_account_id": seller_account_id,
        "markup_percentage": markup_percentage,
        **custom_overrides,
    }

    product_item = ProductItem(**item_data)
    session.add(product_item)
    await session.commit()
    await session.refresh(product_item)

    return product_item


async def get_effective_values(
    session: AsyncSession, product_item_id: GUID
) -> Optional[Dict[str, Any]]:
    """
    Get the effective computed values for a ProductItem.

    Args:
        session: Database session
        product_item_id: ID of the product item

    Returns:
        Dictionary with effective values or None if not found
    """
    query = ProductItemQueries.get_effective_values_query(product_item_id)
    result = await session.exec(query)
    row = result.first()

    if row is None:
        return None

    product_item, _ = row

    return {
        "id": product_item.id,
        "name": product_item.name,
        "description": product_item.description,
        "price": product_item.price,
        "currency_id": product_item.currency_id,
        "category_id": product_item.category_id,
        "status": product_item.status,
        "is_digital": product_item.is_digital,
        "attributes": product_item.attributes,
    }
