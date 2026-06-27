from __future__ import annotations


class TokenizerService:
    """Lightweight tokenizer fallback used when Hugging Face deps are absent."""

    def __init__(self) -> None:
        self.loaded = False
        self.backend = "fallback"
        self._tokenizer = None

    def load(self, model_name: str) -> None:
        try:
            from transformers import AutoTokenizer  # type: ignore

            self._tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
            self.backend = "transformers"
            self.loaded = True
        except Exception:
            self._tokenizer = None
            self.backend = "fallback"
            self.loaded = True

    def encode(self, text: str) -> list[int]:
        if self._tokenizer is not None:
            return list(self._tokenizer.encode(text))
        return [len(token) for token in text.split() if token]

    def decode(self, token_ids: list[int]) -> str:
        if self._tokenizer is not None:
            return self._tokenizer.decode(token_ids, skip_special_tokens=True)
        return " ".join(f"tok{token_id}" for token_id in token_ids)

