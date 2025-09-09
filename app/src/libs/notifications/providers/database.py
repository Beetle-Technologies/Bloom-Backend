from typing import Any, Dict

from src.libs.notifications.interface import NotificationProvider


class DatabaseProvider(NotificationProvider):
    async def send(self, account_id: str, data: Dict[str, Any]) -> bool:
        # Logic to store in database (e.g., create a record or log)
        # For now, just return True
        return True
