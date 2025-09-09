from typing import Any, Dict

from src.core.types import GUID
from src.libs.notifications.interface import NotificationProvider


class EmailProvider(NotificationProvider):
    async def send(self, account_id: GUID, data: Dict[str, Any]) -> bool:
        # Use your email service (e.g., SMTP or SES)
        # Render template and send
        # For now, mock
        return True
