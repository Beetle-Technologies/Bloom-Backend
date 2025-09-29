from typing import Any

from src.core.config import settings
from src.core.logging import get_logger
from src.libs.cache.exceptions import CacheConfigurationError
from src.libs.cache.interface import CacheProvider
from src.libs.cache.providers.memory import MemoryCacheProvider
from src.libs.cache.providers.redis import RedisCacheProvider
from src.libs.cache.schemas import MemoryCacheConfiguration, RedisCacheConfiguration

logger = get_logger(__name__)


class CacheFactory:
    """
    Factory for creating cache providers based on environment and configuration.
    """

    _providers: dict[str, type[CacheProvider]] = {
        "memory": MemoryCacheProvider,
        "redis": RedisCacheProvider,
    }

    @classmethod
    def register_provider(cls, name: str, provider_class: type[CacheProvider]) -> None:
        """
        Register a custom cache provider.

        Args:
            name: Provider name
            provider_class: Provider class
        """
        cls._providers[name] = provider_class

    @classmethod
    def create_provider(cls, provider_type: str, config: Any) -> CacheProvider:
        """
        Create a provider instance.

        Args:
            provider_type: Type of provider to create
            config: Provider configuration

        Returns:
            An instance of the requested provider

        Raises:
            CacheConfigurationError: If the provider type is not supported
        """
        if provider_type not in cls._providers:
            raise CacheConfigurationError(f"Unsupported cache provider type: {provider_type}")

        provider_class = cls._providers[provider_type]
        return provider_class(config)  # type: ignore

    @classmethod
    def get_configured_provider(cls) -> CacheProvider:
        """
        Get the configured cache provider based on environment settings.

        Returns:
            An instance of the configured cache provider
        """
        # Determine provider type based on environment
        if settings.ENVIRONMENT == "local":
            provider_type = "memory"
        else:
            provider_type = "redis"

        logger.info(f"Creating cache provider: {provider_type} for environment: {settings.ENVIRONMENT}")

        if provider_type == "memory":
            config = MemoryCacheConfiguration(
                default_ttl=settings.CACHE_DEFAULT_TTL,
                key_prefix=settings.CACHE_KEY_PREFIX,
                max_size=settings.CACHE_MEMORY_MAX_SIZE,
                cleanup_interval=settings.CACHE_MEMORY_CLEANUP_INTERVAL,
            )
            return cls.create_provider("memory", config)

        elif provider_type == "redis":
            config = RedisCacheConfiguration(
                default_ttl=settings.CACHE_DEFAULT_TTL,
                key_prefix=settings.CACHE_KEY_PREFIX,
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.CACHE_REDIS_DB,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            return cls.create_provider("redis", config)

        else:
            raise CacheConfigurationError(f"Unsupported cache provider: {provider_type}")

    @classmethod
    def create_custom_provider(
        cls, provider_type: str, config_overrides: dict[str, Any] | None = None
    ) -> CacheProvider:
        """
        Create a cache provider with custom configuration.

        Args:
            provider_type: Type of provider to create ("memory" or "redis")
            config_overrides: Configuration overrides

        Returns:
            An instance of the cache provider with custom configuration
        """
        config_overrides = config_overrides or {}

        if provider_type == "memory":
            default_config = {
                "default_ttl": settings.CACHE_DEFAULT_TTL,
                "key_prefix": settings.CACHE_KEY_PREFIX,
                "max_size": settings.CACHE_MEMORY_MAX_SIZE,
                "cleanup_interval": settings.CACHE_MEMORY_CLEANUP_INTERVAL,
            }
            default_config.update(config_overrides)
            config = MemoryCacheConfiguration(**default_config)
            return cls.create_provider("memory", config)

        elif provider_type == "redis":
            default_config = {
                "default_ttl": settings.CACHE_DEFAULT_TTL,
                "key_prefix": settings.CACHE_KEY_PREFIX,
                "host": settings.REDIS_HOST,
                "port": settings.REDIS_PORT,
                "password": settings.REDIS_PASSWORD,
                "db": settings.CACHE_REDIS_DB,
                "socket_timeout": 5,
                "socket_connect_timeout": 5,
                "retry_on_timeout": True,
                "health_check_interval": 30,
            }
            default_config.update(config_overrides)
            config = RedisCacheConfiguration(**default_config)
            return cls.create_provider("redis", config)

        else:
            raise CacheConfigurationError(f"Unsupported cache provider: {provider_type}")
