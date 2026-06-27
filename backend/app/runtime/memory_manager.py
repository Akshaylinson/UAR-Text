from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field


@dataclass
class MemorySnapshot:
    ram_usage_percent: float = 0.0
    ram_free_gb: float = 0.0
    ram_total_gb: float = 0.0
    active_layers: list[int] = field(default_factory=list)


class MemoryManager:
    def __init__(self, unload_threshold: float = 0.8) -> None:
        self.unload_threshold = unload_threshold
        self.layer_cache: OrderedDict[int, float] = OrderedDict()

    def track_layer(self, layer_id: int) -> None:
        self.layer_cache[layer_id] = 0.0
        self.layer_cache.move_to_end(layer_id)

    def evict_if_needed(self, ram_usage_percent: float) -> list[int]:
        evicted: list[int] = []
        if ram_usage_percent > self.unload_threshold * 100:
            while len(self.layer_cache) > 1:
                layer_id, _ = self.layer_cache.popitem(last=False)
                evicted.append(layer_id)
        return evicted

