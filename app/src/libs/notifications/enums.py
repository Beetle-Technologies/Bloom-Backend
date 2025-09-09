from enum import StrEnum


class NotificationDeliveryMethod(StrEnum):
    """
    Enumeration of delivery methods for notifications.

    Attributes:
        DATABASE: Database delivery method.
        EMAIL: Email delivery method.
        PUSH: Push notification delivery method.
    """

    DATABASE = "database"
    EMAIL = "email"
    PUSH = "push"


class NotificationStatus(StrEnum):
    """
    Enumeration of notification statuses.

    Attributes:
        PENDING: Notification is pending.
        SENT: Notification has been sent.
        FAILED: Notification delivery failed.
    """

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
