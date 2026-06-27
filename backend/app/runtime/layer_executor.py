from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    hidden_state: list[float]
    logits: list[float]


class LayerExecutor:
    def execute(self, token_ids: list[int], layer_ids: list[int]) -> ExecutionResult:
        hidden = [float(token_id) for token_id in token_ids] or [0.0]
        for layer_id in layer_ids:
            hidden = [
                math.tanh((value + (layer_id + 1)) / (index + 2))
                for index, value in enumerate(hidden)
            ]
        logits = [round(value * 100.0, 4) for value in hidden[: min(16, len(hidden))]]
        return ExecutionResult(hidden_state=hidden, logits=logits)

