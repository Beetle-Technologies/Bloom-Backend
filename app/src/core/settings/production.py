from typing import Literal

from pydantic_settings import SettingsConfigDict

from .base import Settings as BaseSettings


class Settings(BaseSettings):
    """Settings to use in a production environment."""

    model_config = SettingsConfigDict(
        env_file=".env/.env.production",
        env_ignore_empty=True,
        extra="ignore",
    )

    ENVIRONMENT: Literal["local", "staging", "production"] = "production"
