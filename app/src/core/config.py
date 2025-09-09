from enum import StrEnum
from functools import lru_cache

from src.core.settings.base import Settings as BaseSettings
from src.core.settings.local import Settings as LocalSettings
from src.core.settings.production import Settings as ProductionSettings
from src.core.settings.staging import Settings as StagingSettings


class Environment(StrEnum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


@lru_cache
def _get_settings() -> BaseSettings:
    """
    Returns the appropriate settings based on the environment.

    Args:
        environment (str): The current environment (local, staging, or production)

    Returns:
        BaseSettings: The settings for the specified environment

    Raises:
        ValueError: If an invalid environment is specified
    """

    environment = Environment(BaseSettings().ENVIRONMENT.lower())  # type: ignore

    settings_map = {
        Environment.LOCAL: LocalSettings,
        Environment.STAGING: StagingSettings,
        Environment.PRODUCTION: ProductionSettings,
    }

    if environment not in settings_map:
        raise ValueError(
            f"Invalid environment: {environment.value}. "
            f"Must be one of {', '.join(env.value for env in Environment)}"
        )

    return settings_map[environment]()  # type: ignore


settings = _get_settings()
