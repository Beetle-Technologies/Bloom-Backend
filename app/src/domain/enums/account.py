from enum import StrEnum


class AccountTypeEnum(StrEnum):
    """
    Enumeration representing the various types of accounts in the system.

    Attributes:\n
        ADMIN: Represents an admin account.
        BUSINESS: Represents a business account.
        SUPPLIER: Represents a supplier account.
        USER: Represents a customer account.
    """

    ADMIN = "admin"
    BUSINESS = "business"
    SUPPLIER = "supplier"
    USER = "user"

    def is_user(self) -> bool:
        """Check if the account type is USER."""
        return self == AccountTypeEnum.USER

    def is_admin(self) -> bool:
        """Check if the account type is ADMIN."""
        return self == AccountTypeEnum.ADMIN

    def is_business(self) -> bool:
        """Check if the account type is BUSINESS."""
        return self == AccountTypeEnum.BUSINESS

    def is_supplier(self) -> bool:
        """Check if the account type is SUPPLIER."""
        return self == AccountTypeEnum.SUPPLIER
