from typing import Literal

from pydantic_settings import SettingsConfigDict

from .base import Settings as BaseSettings


class Settings(BaseSettings):
    """Note this setting is to only be used during testing and low/medium resource environments."""

    model_config = SettingsConfigDict(
        env_file=".env/.env.staging",
        env_ignore_empty=True,
        extra="ignore",
    )

    ENVIRONMENT: Literal["local", "staging", "production"] = "staging"
