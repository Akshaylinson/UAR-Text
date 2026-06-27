from __future__ import annotations

from collections import OrderedDict


class CacheManager:
    def __init__(self, max_items: int = 8) -> None:
        self.max_items = max_items
        self.cache: OrderedDict[str, object] = OrderedDict()

    def set(self, key: str, value: object) -> None:
        self.cache[key] = value
        self.cache.move_to_end(key)
        while len(self.cache) > self.max_items:
            self.cache.popitem(last=False)

    def get(self, key: str) -> object | None:
        value = self.cache.get(key)
        if value is not None:
            self.cache.move_to_end(key)
        return value

