from typing import Literal

from .base import Settings as BaseSettings


class Settings(BaseSettings):
    """Note this setting is to only be used during testing and low/medium resource environments."""

    ENVIRONMENT: Literal["local", "staging", "production"] = "staging"
