import json
import logging
from typing import Any, List, Optional

try:
    import redis.asyncio as redis
    from redis.exceptions import ConnectionError as RedisConnectionError
    from redis.exceptions import RedisError
except ImportError:
    redis = None
    RedisError = Exception
    RedisConnectionError = Exception

from src.libs.cache.exceptions import (
    CacheConfigurationError,
    CacheConnectionError,
    CacheKeyError,
    CacheSerializationError,
)
from src.libs.cache.interface import CacheProvider
from src.libs.cache.schemas import CacheResponse, RedisCacheConfiguration

logger = logging.getLogger(__name__)


class RedisCacheProvider(CacheProvider):
    """
    Redis cache provider with connection pooling and error handling.
    """

    def __init__(self, config: RedisCacheConfiguration) -> None:
        if redis is None:
            raise CacheConfigurationError("Redis is not available. Please install redis package: pip install redis")

        super().__init__(config)
        self.config: RedisCacheConfiguration = config
        self._client: Optional[Any] = None
        self._connection_pool: Optional[Any] = None

    async def _get_client(self) -> Any:
        """Get or create Redis client."""
        if self._client is None:
            try:
                if redis is None:
                    raise CacheConnectionError("Redis is not available")

                self._connection_pool = redis.ConnectionPool(
                    host=self.config.host,
                    port=self.config.port,
                    password=self.config.password,
                    db=self.config.db,
                    socket_timeout=self.config.socket_timeout,
                    socket_connect_timeout=self.config.socket_connect_timeout,
                    retry_on_timeout=self.config.retry_on_timeout,
                    health_check_interval=self.config.health_check_interval,
                    decode_responses=True,
                    max_connections=10,
                )

                self._client = redis.Redis(connection_pool=self._connection_pool)

                # Test the connection
                await self._client.ping()
                logger.info("Redis cache provider connected successfully")

            except (RedisConnectionError, RedisError) as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                raise CacheConnectionError(f"Failed to connect to Redis: {str(e)}")

        return self._client

    def _serialize_value(self, value: Any) -> str:
        """Serialize value for Redis storage."""
        try:
            return json.dumps(value, default=str)
        except (TypeError, ValueError) as e:
            raise CacheSerializationError(f"Failed to serialize value: {str(e)}")

    def _deserialize_value(self, serialized: str) -> Any:
        """Deserialize value from Redis storage."""
        try:
            return json.loads(serialized)
        except (TypeError, ValueError) as e:
            raise CacheSerializationError(f"Failed to deserialize value: {str(e)}")

    async def get(self, key: str) -> CacheResponse:
        """Get a value from Redis cache."""
        try:
            self._validate_key(key)
            cache_key = self._build_key(key)
            client = await self._get_client()

            value = await client.get(cache_key)

            if value is None:
                return CacheResponse(success=True, value=None, from_cache=False)

            # Get TTL
            ttl_remaining = await client.ttl(cache_key)
            ttl_remaining = ttl_remaining if ttl_remaining > 0 else None

            return CacheResponse(
                success=True,
                value=self._deserialize_value(value),
                from_cache=True,
                ttl_remaining=ttl_remaining,
            )

        except (CacheSerializationError, CacheKeyError) as e:
            logger.error(f"Cache get operation failed for key {key}: {str(e)}")
            return CacheResponse(success=False, error=str(e))
        except Exception as e:
            logger.error(f"Unexpected error during cache get for key {key}: {str(e)}")
            return CacheResponse(success=False, error=f"Failed to get cache value: {str(e)}")

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> CacheResponse:
        """Set a value in Redis cache."""
        try:
            self._validate_key(key)
            cache_key = self._build_key(key)
            client = await self._get_client()

            # Use default TTL if not provided
            if ttl is None:
                ttl = self.config.default_ttl

            serialized_value = self._serialize_value(value)

            if ttl > 0:
                await client.setex(cache_key, ttl, serialized_value)
            else:
                await client.set(cache_key, serialized_value)

            return CacheResponse(success=True)

        except (CacheSerializationError, CacheKeyError) as e:
            logger.error(f"Cache set operation failed for key {key}: {str(e)}")
            return CacheResponse(success=False, error=str(e))
        except Exception as e:
            logger.error(f"Unexpected error during cache set for key {key}: {str(e)}")
            return CacheResponse(success=False, error=f"Failed to set cache value: {str(e)}")

    async def delete(self, key: str) -> CacheResponse:
        """Delete a value from Redis cache."""
        try:
            self._validate_key(key)
            cache_key = self._build_key(key)
            client = await self._get_client()

            await client.delete(cache_key)
            return CacheResponse(success=True)

        except CacheKeyError as e:
            logger.error(f"Cache delete operation failed for key {key}: {str(e)}")
            return CacheResponse(success=False, error=str(e))
        except Exception as e:
            logger.error(f"Unexpected error during cache delete for key {key}: {str(e)}")
            return CacheResponse(success=False, error=f"Failed to delete cache value: {str(e)}")

    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis cache."""
        try:
            self._validate_key(key)
            cache_key = self._build_key(key)
            client = await self._get_client()

            result = await client.exists(cache_key)
            return bool(result)

        except Exception as e:
            logger.error(f"Cache exists operation failed for key {key}: {str(e)}")
            return False

    async def clear(self, pattern: Optional[str] = None) -> CacheResponse:
        """Clear cache entries matching pattern."""
        try:
            client = await self._get_client()

            if pattern is None:
                # Clear all keys with the configured prefix
                pattern = f"{self.config.key_prefix}:*"
            else:
                pattern = self._build_key(pattern)

            # Use SCAN to avoid blocking the Redis server with large datasets
            keys_to_delete: List[str] = []
            async for key in client.scan_iter(match=pattern, count=100):
                keys_to_delete.append(key)

            if keys_to_delete:
                await client.delete(*keys_to_delete)

            return CacheResponse(success=True)
        except Exception as e:
            logger.error(f"Unexpected error during cache clear: {str(e)}")
            return CacheResponse(success=False, error=f"Failed to clear cache: {str(e)}")

    async def ttl(self, key: str) -> Optional[int]:
        """Get the time to live for a key in Redis."""
        try:
            self._validate_key(key)
            cache_key = self._build_key(key)
            client = await self._get_client()

            ttl_value = await client.ttl(cache_key)

            if ttl_value == -2:  # Key doesn't exist
                return None
            elif ttl_value == -1:  # Key exists but has no expiry
                return -1
            else:
                return ttl_value

        except Exception as e:
            logger.error(f"Cache TTL operation failed for key {key}: {str(e)}")
            return None

    async def health_check(self) -> bool:
        """Check if Redis is healthy and accessible."""
        try:
            client = await self._get_client()
            await client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False

    async def close(self) -> None:
        """Close Redis connections."""
        if self._client:
            await self._client.close()
            self._client = None

        if self._connection_pool:
            await self._connection_pool.disconnect()
            self._connection_pool = None

    async def get_stats(self) -> dict:
        """Get Redis cache statistics."""
        try:
            client = await self._get_client()
            info = await client.info()

            return {
                "provider_type": "redis",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
            }

        except Exception as e:
            logger.error(f"Failed to get Redis stats: {str(e)}")
            return {"provider_type": "redis", "error": str(e)}
