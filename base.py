"""
Disk-backed cache for search responses. Avoids hammering sites and keeps
the comparator fast on repeat queries.

Swap in Redis for a multi-instance production deploy:
    import redis.asyncio as redis
    r = redis.from_url("redis://localhost:6379/0")
"""
import json
from typing import Optional, Any
import diskcache

from app.core.config import settings

_cache = diskcache.Cache(settings.cache_dir, size_limit=int(5e8))  # 500 MB


def cache_get(key: str) -> Optional[Any]:
    return _cache.get(key)


def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> None:
    _cache.set(key, value, expire=ttl or settings.cache_ttl_seconds)


def cache_clear() -> None:
    _cache.clear()
