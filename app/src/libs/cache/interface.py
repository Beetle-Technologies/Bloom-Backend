from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from src.libs.cache.schemas import CacheResponse


class CacheProvider(ABC):
    """
    Base abstract class for all cache providers.
    """

    def __init__(self, config: Any) -> None:
        """Initialize cache provider with configuration."""
        self.config = config

    @abstractmethod
    async def get(self, key: str) -> "CacheResponse":
        """
        Get a value from the cache.

        Args:
            key (str): The cache key

        Returns:
            CacheResponse: Response object containing the cached value and metadata
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> "CacheResponse":
        """
        Set a value in the cache.

        Args:
            key (str): The cache key
            value (Any): The value to cache
            ttl (Optional[int]): Time to live in seconds (optional)

        Returns:
            CacheResponse: Response object indicating success/failure
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> "CacheResponse":
        """
        Delete a value from the cache.

        Args:
            key (str): The cache key to delete

        Returns:
            CacheResponse: Response object indicating success/failure
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: The cache key to check

        Returns:
            bool: True if key exists, False otherwise
        """
        pass

    @abstractmethod
    async def clear(self, pattern: Optional[str] = None) -> "CacheResponse":
        """
        Clear cache entries.

        Args:
            pattern (Optional[str]): Optional pattern to match keys (e.g., "user:*")
                    If None, clears all keys with the configured prefix

        Returns:
            CacheResponse: Response object indicating success/failure
        """
        pass

    @abstractmethod
    async def ttl(self, key: str) -> Optional[int]:
        """
        Get the time to live for a key.

        Args:
            key (str): The cache key

        Returns:
            Optional[int]: TTL in seconds, None if key doesn't exist or has no expiry
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the cache provider is healthy and accessible.

        Returns:
            bool: True if healthy, False otherwise
        """
        pass

    async def close(self) -> None:
        """
        Close connections and clean up resources.
        """
        pass

    async def get_stats(self) -> dict:
        """
        Get cache provider statistics.
        """
        return {
            "provider_type": "unknown",
            "key_prefix": getattr(self.config, "key_prefix", "unknown"),
        }

    def _build_key(self, key: str) -> str:
        """
        Build the full cache key with prefix.

        Args:
            key (str): The base cache key

        Returns:
            str: The full cache key with prefix
        """
        return f"{self.config.key_prefix}:{key}"

    def _validate_key(self, key: str) -> None:
        """
        Validate cache key format.

        Args:
            key (str): The cache key to validate

        Raises:
            CacheKeyError: If key is invalid
        """
        from src.libs.cache.exceptions import CacheKeyError

        if not key or not isinstance(key, str):
            raise CacheKeyError("Cache key must be a non-empty string")

        if len(key) > 250:
            raise CacheKeyError("Cache key must be 250 characters or less")

        invalid_chars = [" ", "\n", "\r", "\t"]
        if any(char in key for char in invalid_chars):
            raise CacheKeyError("Cache key cannot contain spaces or newline characters")
