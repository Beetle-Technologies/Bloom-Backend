from enum import StrEnum


class BankAccountType(StrEnum):
    """Enumeration of bank account types."""

    CHECKING = "checking"
    SAVINGS = "savings"
    BUSINESS_CHECKING = "business_checking"
    BUSINESS_SAVINGS = "business_savings"
    MONEY_MARKET = "money_market"
    CERTIFICATE_OF_DEPOSIT = "certificate_of_deposit"
    JOINT = "joint"
    TRUST = "trust"
    OTHER = "other"


class BankingInfoStatus(StrEnum):
    """Enumeration of banking info verification statuses."""

    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
