from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass


@dataclass
class RuntimeLayer:
    layer_id: int
    loaded: bool = False
    cached: bool = False


class LayerLoader:
    def __init__(self, max_active_layers: int = 4) -> None:
        self.max_active_layers = max_active_layers
        self.active_layers: OrderedDict[int, RuntimeLayer] = OrderedDict()

    def load_layer(self, layer_id: int) -> RuntimeLayer:
        layer = self.active_layers.get(layer_id, RuntimeLayer(layer_id=layer_id))
        layer.loaded = True
        layer.cached = True
        self.active_layers[layer_id] = layer
        self.active_layers.move_to_end(layer_id)
        self._enforce_limit()
        return layer

    def unload_layer(self, layer_id: int) -> None:
        layer = self.active_layers.get(layer_id)
        if layer:
            layer.loaded = False
            layer.cached = False
            self.active_layers.pop(layer_id, None)

    def preload_next_layer(self, layer_id: int) -> RuntimeLayer:
        return self.load_layer(layer_id)

    def _enforce_limit(self) -> None:
        while len(self.active_layers) > self.max_active_layers:
            oldest_layer_id, oldest_layer = self.active_layers.popitem(last=False)
            oldest_layer.loaded = False
            oldest_layer.cached = False

    def list_loaded_layers(self) -> list[int]:
        return list(self.active_layers.keys())

