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
