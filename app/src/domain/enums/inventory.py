from enum import StrEnum


class InventoryActionType(StrEnum):
    """
    Enumeration for types of inventory actions

    Attributes:
        STOCK_IN: Represents a stock-in action.
        STOCK_OUT: Represents a stock-out action.
        ADJUSTMENT: Represents an inventory adjustment action.
        TRANSFER: Represents a stock transfer action.
        DAMAGED: Represents a damaged inventory item.
        RETURNED: Represents a returned inventory item.
    """

    STOCK_IN = "stock_in"
    STOCK_OUT = "stock_out"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    DAMAGED = "damaged"
    RETURNED = "returned"


class InventoriableType:
    """
    Enumeration for types of inventoriable items.

    Attributes:
        PRODUCT: Represents a product item.
        PRODUCT_ITEM: Represents a product item.
    """

    PRODUCT = "Product"
    PRODUCT_ITEM = "ProductItem"
