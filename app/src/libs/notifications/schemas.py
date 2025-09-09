from typing import Any

from pydantic import BaseModel
from src.core.types import GUID
from src.libs.notifications.enums import NotificationDeliveryMethod


class NotificationCreate(BaseModel):
    """
    Schema for creating a notification.

    Attributes:
        account_id (GUID): The ID of the account associated with the notification.
        type (str): The type of the notification.
        data (dict[str, Any]): The data payload for the notification.
        delivery_methods (list[NotificationDeliveryMethod]): List of methods through which the notification will be delivered.
    """

    account_id: GUID
    type: str
    data: dict[str, Any]
    delivery_methods: list[NotificationDeliveryMethod]


class NotificationPreferenceCreate(BaseModel):
    """
    Schema for creating notification preferences.

    Attributes:
        account_type_info_id (GUID): The ID of the account type information.
        notification_type (str): The type of the notification.
        enabled_methods (list[NotificationDeliveryMethod]): List of enabled delivery methods for the notification.
    """

    account_type_info_id: GUID
    notification_type: str
    enabled_methods: list[NotificationDeliveryMethod]
    is_enabled: bool = True
