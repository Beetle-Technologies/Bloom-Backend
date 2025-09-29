from typing import Optional

from pydantic import BaseModel
from src.core.enums import ClientPlatform, ClientType


class BloomClientInfo(BaseModel):
    """Model representing the parsed X-Bloom-Client header information."""

    platform: ClientPlatform
    version: str
    app: ClientType
    build: Optional[str] = None

    class Config:
        frozen = True

    def __str__(self) -> str:
        parts = [
            f"platform={self.platform}",
            f"version={self.version}",
            f"app={self.app}",
        ]
        if self.build:
            parts.append(f"build={self.build}")
        return "; ".join(parts)

    def is_user_client(self) -> bool:
        """Check if the client is a user client (not an internal service)."""
        return self.app == ClientType.BLOOM_MAIN and self.platform == ClientPlatform.WEB

    def is_supplier_client(self) -> bool:
        """Check if the client is a supplier client."""
        return self.app == ClientType.BLOOM_SUPPLIER and (
            self.platform == ClientPlatform.ANDROID or self.platform == ClientPlatform.IOS
        )

    def is_admin_client(self) -> bool:
        """Check if the client is an admin client."""
        return self.app == ClientType.BLOOM_ADMIN and self.platform == ClientPlatform.WEB

    def is_seller_client(self) -> bool:
        """Check if the client is a seller client."""
        return self.app == ClientType.BLOOM_BUSINESS and (
            self.platform == ClientPlatform.ANDROID or self.platform == ClientPlatform.IOS
        )
