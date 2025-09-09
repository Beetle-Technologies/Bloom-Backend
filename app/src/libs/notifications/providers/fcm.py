from typing import Any, Dict

from src.core.types import GUID
from src.libs.notifications.interface import NotificationProvider


class FCMProvider(NotificationProvider):
    async def send(self, account_id: GUID, data: Dict[str, Any]) -> bool:
        # Use Firebase Cloud Messaging
        # Send push notification
        # For now, mock
        return True
