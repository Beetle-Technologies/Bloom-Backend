from limits import RateLimitItem, WindowStats, parse
from limits.aio.storage.base import Storage
from limits.aio.strategies import MovingWindowRateLimiter, RateLimiter
from src.core.config import settings
from src.libs.throttler.limiter_storage import get_limiter_storage


class LimiterConfig:
    def __init__(
        self,
        environment: str,
        default_limit: str = "100/minute",
        namespace_limits: dict[str, str] | None = None,
    ) -> None:
        self.environment = environment
        self.default_limit = default_limit
        self.namespace_limits = namespace_limits or {}
        self.storage: Storage = get_limiter_storage(environment)
        self.rate_limiters: dict[str, RateLimiter] = {}

    def _get_rate_limit_for_namespace(self, namespace: str) -> RateLimitItem:
        """Get rate limit for a specific namespace"""
        limit_str = self.namespace_limits.get(namespace, self.default_limit)
        return parse(limit_str)

    def _get_rate_limiter(self, namespace: str) -> RateLimiter:
        """Get or create rate limiter for namespace"""
        if namespace not in self.rate_limiters:
            self.rate_limiters[namespace] = MovingWindowRateLimiter(self.storage)
        return self.rate_limiters[namespace]

    async def hit(self, namespace: str, client_key: str, custom_limit: str | None = None) -> bool:
        """Check and apply rate limit"""
        rate_limiter = self._get_rate_limiter(namespace)
        limit_item = parse(custom_limit) if custom_limit else self._get_rate_limit_for_namespace(namespace)
        return await rate_limiter.hit(limit_item, f"{namespace}:{client_key}")

    async def get_window_stats_with_limit(
        self, namespace: str, client_key: str, custom_limit: str | None = None
    ) -> tuple[WindowStats, int]:
        """Get current window statistics with the limit amount"""
        rate_limiter = self._get_rate_limiter(namespace)
        limit_item = parse(custom_limit) if custom_limit else self._get_rate_limit_for_namespace(namespace)
        stats = await rate_limiter.get_window_stats(limit_item, f"{namespace}:{client_key}")
        return stats, limit_item.amount


limiter = LimiterConfig(
    environment=settings.ENVIRONMENT,
    default_limit=f"{settings.RATE_LIMIT_PER_MINUTE}/minute",
)
