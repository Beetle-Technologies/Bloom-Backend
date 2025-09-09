class CacheError(Exception):
    """Base exception for cache operations."""

    def __init__(self, message: str = "Cache operation failed") -> None:
        super().__init__(message)
        self.message = message


class CacheConnectionError(CacheError):
    """Raised when cache connection fails."""

    def __init__(self, message: str = "Failed to connect to cache") -> None:
        super().__init__(message)


class CacheSerializationError(CacheError):
    """Raised when cache serialization/deserialization fails."""

    def __init__(self, message: str = "Cache serialization failed") -> None:
        super().__init__(message)


class CacheKeyError(CacheError):
    """Raised when cache key is invalid."""

    def __init__(self, message: str = "Invalid cache key") -> None:
        super().__init__(message)


class CacheConfigurationError(CacheError):
    """Raised when cache configuration is invalid."""

    def __init__(self, message: str = "Invalid cache configuration") -> None:
        super().__init__(message)
