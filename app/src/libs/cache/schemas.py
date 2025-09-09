from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CacheConfiguration:
    """Base cache configuration."""

    default_ttl: int = 3600  # 1 hour
    key_prefix: str = "bloom_cache"


@dataclass
class MemoryCacheConfiguration(CacheConfiguration):
    """In-memory cache configuration."""

    max_size: int = 1000  # Maximum number of items to store
    cleanup_interval: int = 300  # Cleanup interval in seconds (5 minutes)


@dataclass
class RedisCacheConfiguration(CacheConfiguration):
    """Redis cache configuration."""

    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 1
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30


@dataclass
class CacheItem:
    """Cache item with metadata."""

    key: str
    value: Any
    ttl: Optional[int] = None
    created_at: Optional[float] = None
    expires_at: Optional[float] = None


@dataclass
class CacheResponse:
    """Response object for cache operations."""

    success: bool
    value: Any = None
    error: Optional[str] = None
    from_cache: bool = False
    ttl_remaining: Optional[int] = None
