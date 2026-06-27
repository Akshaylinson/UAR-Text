from __future__ import annotations

from ..runtime.runtime_controller import RuntimeController


class InferenceService:
    def __init__(self, runtime: RuntimeController) -> None:
        self.runtime = runtime

    def generate(self, prompt: str, max_new_tokens: int = 64) -> dict:
        return self.runtime.generate(prompt, max_new_tokens=max_new_tokens)

