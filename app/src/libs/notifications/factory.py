from src.libs.notifications.enums import NotificationDeliveryMethod
from src.libs.notifications.interface import NotificationProvider
from src.libs.notifications.providers.database import DatabaseProvider
from src.libs.notifications.providers.email import EmailProvider
from src.libs.notifications.providers.fcm import FCMProvider


class NotificationFactory:
    @staticmethod
    def get_provider(method: NotificationDeliveryMethod) -> NotificationProvider:
        if method == NotificationDeliveryMethod.DATABASE:
            return DatabaseProvider()
        elif method == NotificationDeliveryMethod.EMAIL:
            return EmailProvider()
        elif method == NotificationDeliveryMethod.PUSH:
            return FCMProvider()
        raise ValueError(f"Unsupported delivery method: {method}")
