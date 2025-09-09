import asyncio
import json
import time
from threading import RLock
from typing import Any, Dict, Optional

from src.libs.cache.exceptions import CacheSerializationError
from src.libs.cache.interface import CacheProvider
from src.libs.cache.schemas import CacheItem, CacheResponse, MemoryCacheConfiguration


class MemoryCacheProvider(CacheProvider):
    """
    In-memory cache provider using a dictionary with TTL support.
    Thread-safe implementation with background cleanup.
    """

    def __init__(self, config: MemoryCacheConfiguration) -> None:
        super().__init__(config)
        self.config: MemoryCacheConfiguration = config
        self._cache: Dict[str, CacheItem] = {}
        self._lock = RLock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()

    def _start_cleanup_task(self) -> None:
        """Start the background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_keys())

    async def _cleanup_expired_keys(self) -> None:
        """Background task to clean up expired keys."""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._remove_expired_keys()
            except asyncio.CancelledError:
                break
            except Exception:
                # Continue cleanup even if there's an error
                pass

    async def _remove_expired_keys(self) -> None:
        """Remove expired keys from the cache."""
        current_time = time.time()
        expired_keys = []

        with self._lock:
            for key, item in self._cache.items():
                if item.expires_at and item.expires_at <= current_time:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

    def _is_expired(self, item: CacheItem) -> bool:
        """Check if a cache item is expired."""
        if item.expires_at is None:
            return False
        return time.time() > item.expires_at

    def _serialize_value(self, value: Any) -> str:
        """Serialize value for storage."""
        try:
            return json.dumps(value, default=str)
        except (TypeError, ValueError) as e:
            raise CacheSerializationError(f"Failed to serialize value: {str(e)}")

    def _deserialize_value(self, serialized: str) -> Any:
        """Deserialize value from storage."""
        try:
            return json.loads(serialized)
        except (TypeError, ValueError) as e:
            raise CacheSerializationError(f"Failed to deserialize value: {str(e)}")

    async def get(self, key: str) -> CacheResponse:
        """Get a value from the cache."""
        try:
            self._validate_key(key)
            cache_key = self._build_key(key)

            with self._lock:
                item = self._cache.get(cache_key)

                if item is None:
                    return CacheResponse(success=True, value=None, from_cache=False)

                if self._is_expired(item):
                    del self._cache[cache_key]
                    return CacheResponse(success=True, value=None, from_cache=False)

                # Calculate remaining TTL
                ttl_remaining = None
                if item.expires_at:
                    ttl_remaining = max(0, int(item.expires_at - time.time()))

                return CacheResponse(
                    success=True,
                    value=self._deserialize_value(item.value),
                    from_cache=True,
                    ttl_remaining=ttl_remaining,
                )

        except Exception as e:
            return CacheResponse(success=False, error=f"Failed to get cache value: {str(e)}")

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> CacheResponse:
        """Set a value in the cache."""
        try:
            self._validate_key(key)
            cache_key = self._build_key(key)

            # Use default TTL if not provided
            if ttl is None:
                ttl = self.config.default_ttl

            current_time = time.time()
            expires_at = current_time + ttl if ttl > 0 else None

            serialized_value = self._serialize_value(value)

            with self._lock:
                # Check if we need to remove items due to max_size limit
                if len(self._cache) >= self.config.max_size and cache_key not in self._cache:
                    await self._evict_items(1)

                self._cache[cache_key] = CacheItem(
                    key=cache_key,
                    value=serialized_value,
                    ttl=ttl,
                    created_at=current_time,
                    expires_at=expires_at,
                )

            return CacheResponse(success=True)

        except Exception as e:
            return CacheResponse(success=False, error=f"Failed to set cache value: {str(e)}")

    async def _evict_items(self, count: int) -> None:
        """Evict the oldest items from the cache (LRU-like behavior)."""
        if not self._cache:
            return

        # Sort by created_at and remove oldest items
        sorted_items = sorted(self._cache.items(), key=lambda x: x[1].created_at or 0)

        for i in range(min(count, len(sorted_items))):
            key = sorted_items[i][0]
            del self._cache[key]

    async def delete(self, key: str) -> CacheResponse:
        """Delete a value from the cache."""
        try:
            self._validate_key(key)
            cache_key = self._build_key(key)

            with self._lock:
                if cache_key in self._cache:
                    del self._cache[cache_key]

            return CacheResponse(success=True)

        except Exception as e:
            return CacheResponse(success=False, error=f"Failed to delete cache value: {str(e)}")

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        try:
            self._validate_key(key)
            cache_key = self._build_key(key)

            with self._lock:
                item = self._cache.get(cache_key)
                if item is None:
                    return False

                if self._is_expired(item):
                    del self._cache[cache_key]
                    return False

                return True

        except Exception:
            return False

    async def clear(self, pattern: Optional[str] = None) -> CacheResponse:
        """Clear cache entries."""
        try:
            with self._lock:
                if pattern is None:
                    # Clear all keys with the configured prefix
                    keys_to_delete = [key for key in self._cache.keys() if key.startswith(f"{self.config.key_prefix}:")]
                else:
                    # Simple pattern matching (supports * wildcard)
                    import fnmatch

                    full_pattern = self._build_key(pattern)
                    keys_to_delete = [key for key in self._cache.keys() if fnmatch.fnmatch(key, full_pattern)]

                for key in keys_to_delete:
                    del self._cache[key]

            return CacheResponse(success=True)

        except Exception as e:
            return CacheResponse(success=False, error=f"Failed to clear cache: {str(e)}")

    async def ttl(self, key: str) -> Optional[int]:
        """Get the time to live for a key."""
        try:
            self._validate_key(key)
            cache_key = self._build_key(key)

            with self._lock:
                item = self._cache.get(cache_key)
                if item is None or self._is_expired(item):
                    return None

                if item.expires_at is None:
                    return -1  # No expiry

                return max(0, int(item.expires_at - time.time()))

        except Exception:
            return None

    async def health_check(self) -> bool:
        """Check if the cache provider is healthy."""
        try:
            # Test basic operations
            test_key = "health_check_test"
            await self.set(test_key, "test_value", ttl=1)
            result = await self.get(test_key)
            await self.delete(test_key)
            return result.success and result.value == "test_value"
        except Exception:
            return False

    async def close(self) -> None:
        """Clean up resources."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        with self._lock:
            self._cache.clear()

    async def get_stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            return {
                "total_keys": len(self._cache),
                "max_size": self.config.max_size,
                "cleanup_interval": self.config.cleanup_interval,
                "provider_type": "memory",
            }
