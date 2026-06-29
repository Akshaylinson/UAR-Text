from __future__ import annotations

from collections import OrderedDict


class CacheManager:
    def __init__(self, max_items: int = 8) -> None:
        self.max_items = max_items
        self.cache: OrderedDict[str, object] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def set(self, key: str, value: object) -> None:
        self.cache[key] = value
        self.cache.move_to_end(key)
        while len(self.cache) > self.max_items:
            self.cache.popitem(last=False)

    def get(self, key: str) -> object | None:
        value = self.cache.get(key)
        if value is not None:
            self.hits += 1
            self.cache.move_to_end(key)
            return value
        self.misses += 1
        return None

    def stats(self) -> dict[str, float | int]:
        total = self.hits + self.misses
        hit_ratio = round((self.hits / total) * 100.0, 2) if total else 0.0
        miss_ratio = round((self.misses / total) * 100.0, 2) if total else 0.0
        return {
            "max_items": self.max_items,
            "current_items": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": hit_ratio,
            "miss_ratio": miss_ratio,
        }
