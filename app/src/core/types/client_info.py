from typing import Optional

from pydantic import BaseModel
from src.core.enums import AppName, Platform


class BloomClientInfo(BaseModel):
    """Model representing the parsed X-Bloom-Client header information."""

    platform: Platform
    version: str
    app: AppName
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
