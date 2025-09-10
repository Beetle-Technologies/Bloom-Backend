from typing import Literal

from .base import Settings as BaseSettings


class Settings(BaseSettings):
    """Settings to use in a production environment."""

    ENVIRONMENT: Literal["local", "staging", "production"] = "production"
