import asyncio
import functools
import hashlib
from typing import Any, Callable, Optional, ParamSpec, TypeVar

from src.core.logging import get_logger
from src.libs.cache.factory import CacheFactory
from src.libs.cache.interface import CacheProvider

logger = get_logger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


class CacheService:
    """
    High-level cache service providing caching utilities and decorators.
    """

    def __init__(self, provider: Optional[CacheProvider] = None) -> None:
        """
        Initialize cache service.

        Args:
            provider: Cache provider instance. If None, will use factory to create one.
        """
        self._provider = provider or CacheFactory.get_configured_provider()

    @property
    def provider(self) -> CacheProvider:
        """Get the cache provider."""
        return self._provider

    async def get(self, key: str) -> Any:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            response = await self._provider.get(key)
            return response.value if response.success else None
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {str(e)}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        only_if_not_error: bool = True,
    ) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            only_if_not_error: Only cache if value is not an error/exception

        Returns:
            True if successfully cached, False otherwise
        """
        try:
            if only_if_not_error and isinstance(value, (Exception, BaseException)):
                logger.debug(f"Skipping cache for key {key}: value is an exception")
                return False

            response = await self._provider.set(key, value, ttl)
            return response.success
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if successfully deleted, False otherwise
        """
        try:
            response = await self._provider.delete(key)
            return response.success
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {str(e)}")
            return False

    async def clear(self, pattern: Optional[str] = None) -> bool:
        """
        Clear cache entries.

        Args:
            pattern: Pattern to match keys (optional)

        Returns:
            True if successfully cleared, False otherwise
        """
        try:
            response = await self._provider.clear(pattern)
            return response.success
        except Exception as e:
            logger.error(f"Cache clear failed: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            return await self._provider.exists(key)
        except Exception as e:
            logger.error(f"Cache exists check failed for key {key}: {str(e)}")
            return False

    async def get_or_set(
        self,
        key: str,
        factory_func: Callable[[], Any],
        ttl: Optional[int] = None,
        only_if_not_error: bool = True,
    ) -> Any:
        """
        Get value from cache, or set it if not found.

        Args:
            key: Cache key
            factory_func: Function to call if cache miss
            ttl: Time to live in seconds
            only_if_not_error: Only cache if result is not an error

        Returns:
            Cached or computed value
        """
        # Try to get from cache first
        cached_value = await self.get(key)
        if cached_value is not None:
            logger.debug(f"Cache hit for key: {key}")
            return cached_value

        logger.debug(f"Cache miss for key: {key}, computing value")

        # Compute value
        if asyncio.iscoroutinefunction(factory_func):
            value = await factory_func()  # type: ignore
        else:
            value = factory_func()

        # Cache the result
        await self.set(key, value, ttl, only_if_not_error)
        return value

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a cache key based on function arguments.

        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Generated cache key
        """
        # Create a string representation of arguments
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

        # Create hash of the key parts to avoid very long keys
        key_string = "|".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()

        return f"{prefix}:{key_hash}"

    async def health_check(self) -> bool:
        """Check cache provider health."""
        try:
            return await self._provider.health_check()
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            return False

    async def close(self) -> None:
        """Close cache connections."""
        try:
            await self._provider.close()
        except Exception as e:
            logger.error(f"Cache close failed: {str(e)}")


# Decorator functions


def cached(
    ttl: Optional[int] = None,
    key_prefix: Optional[str] = None,
    only_if_not_error: bool = True,
    cache_service: Optional[CacheService] = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to cache function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Cache key prefix. If None, uses function name
        only_if_not_error: Only cache if result is not an error
        cache_service: Cache service instance. If None, creates new one

    Returns:
        Decorated function
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        cache = cache_service or CacheService()
        func_name = key_prefix or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Generate cache key
            cache_key = cache.generate_key(func_name, *args, **kwargs)

            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for function {func_name}")
                return cached_result

            logger.debug(f"Cache miss for function {func_name}")

            # Call the original function
            result = await func(*args, **kwargs)  # type: ignore

            # Cache the result
            await cache.set(cache_key, result, ttl, only_if_not_error)
            return result

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            cache_key = cache.generate_key(func_name, *args, **kwargs)

            try:
                # Call the original function
                result = func(*args, **kwargs)

                # Schedule caching for later (fire and forget)
                asyncio.create_task(cache.set(cache_key, result, ttl, only_if_not_error))
                return result
            except Exception:
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


def cache_invalidate(
    key_prefix: str, cache_service: Optional[CacheService] = None
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to invalidate cache entries after function execution.

    Args:
        key_prefix: Cache key prefix to invalidate
        cache_service: Cache service instance

    Returns:
        Decorated function
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        cache = cache_service or CacheService()

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            result = await func(*args, **kwargs)  # type: ignore
            # Invalidate cache after successful execution
            await cache.clear(f"{key_prefix}:*")
            return result

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            result = func(*args, **kwargs)
            asyncio.create_task(cache.clear(f"{key_prefix}:*"))
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get or create global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


async def setup_cache() -> CacheService:
    """Setup and return cache service."""
    cache_service = get_cache_service()

    is_healthy = await cache_service.health_check()
    if is_healthy:
        logger.info("Cache service initialized successfully")
    else:
        logger.warning("Cache service health check failed")

    return cache_service


async def teardown_cache() -> None:
    """Teardown cache service."""
    global _cache_service
    if _cache_service:
        await _cache_service.close()
        _cache_service = None
