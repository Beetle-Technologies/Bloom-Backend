from enum import StrEnum


class ProductStatus(StrEnum):
    """
    Enumeration for Product status options

    Attributes:
        ACTIVE: Represents an active product.
        INACTIVE: Represents an inactive product.
        DRAFT: Represents a product that is in draft status.
        DISCONTINUED: Represents a product that is no longer available.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    DISCONTINUED = "discontinued"
