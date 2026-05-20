import time
from typing import Any

from bot.config import CACHE_TTL_SECONDS

_store: dict[int, tuple[float, Any]] = {}


def get_cached(group_id: int):
    entry = _store.get(group_id)
    if not entry:
        return None
    expires_at, data = entry
    if time.time() > expires_at:
        _store.pop(group_id, None)
        return None
    return data


def set_cached(group_id: int, data) -> None:
    _store[group_id] = (time.time() + CACHE_TTL_SECONDS, data)


def invalidate(group_id: int) -> None:
    _store.pop(group_id, None)
