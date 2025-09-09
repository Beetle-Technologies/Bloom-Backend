from enum import StrEnum


class OrderStatus(StrEnum):
    """
    Enumeration of Order status options

    Attributes:
        PENDING: Represents a pending order.
        CONFIRMED: Represents a confirmed order.
        PROCESSING: Represents an order that is being processed.
        SHIPPED: Represents an order that has been shipped.
        DELIVERED: Represents an order that has been delivered.
        CANCELLED: Represents an order that has been cancelled.
        REFUNDED: Represents an order that has been refunded.
    """

    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
