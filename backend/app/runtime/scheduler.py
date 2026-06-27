from __future__ import annotations


class Scheduler:
    def __init__(self, version: int = 1) -> None:
        self.version = version

    def plan(self, prompt: str, layer_count: int) -> list[int]:
        if layer_count <= 0:
            return []
        if self.version <= 1:
            return list(range(layer_count))
        prompt_score = sum(ord(char) for char in prompt)
        selected = [index for index in range(layer_count) if (index + prompt_score) % 3 != 0]
        return selected or list(range(layer_count))

