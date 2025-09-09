from abc import ABC, abstractmethod
from typing import Any, Dict

from src.core.types import GUID


class NotificationProvider(ABC):
    @abstractmethod
    async def send(self, account_id: GUID, data: Dict[str, Any]) -> bool:
        pass


class TemplateRenderer(ABC):
    @abstractmethod
    def render(self, template: str, context: Dict[str, Any]) -> str:
        pass
