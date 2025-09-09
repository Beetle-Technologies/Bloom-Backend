from limits.aio.storage.base import Storage
from limits.storage import storage_from_string
from src.core.config import settings


def get_limiter_storage(environment: str) -> Storage:
    """Get appropriate storage backend based on environment"""
    storage_map: dict[str, str] = {
        "local": "async+memory://",
        "staging": f"async+{settings.REDIS_URL}",
        "production": f"async+{settings.REDIS_URL}",
    }

    if environment not in storage_map:
        raise ValueError(f"Invalid environment: {environment}")

    return storage_from_string(storage_map[environment])  # type: ignore
