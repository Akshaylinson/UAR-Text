from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LoadedModel:
    model_name: str
    provider: str
    layer_count: int
    hidden_size: int
    model: Any = None
    tokenizer: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelLoader:
    def __init__(self) -> None:
        self.current: LoadedModel | None = None

    def load_model(self, model_name: str) -> LoadedModel:
        try:
            import torch  # type: ignore
            from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore

            tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                low_cpu_mem_usage=True,
                torch_dtype=torch.float32,
                device_map="cpu",
            )
            layers = getattr(model, "model", None)
            layer_count = len(getattr(layers, "layers", [])) if layers else 0
            hidden_size = int(getattr(model.config, "hidden_size", 0))
            loaded = LoadedModel(
                model_name=model_name,
                provider="transformers",
                layer_count=layer_count,
                hidden_size=hidden_size,
                model=model,
                tokenizer=tokenizer,
                metadata={
                    "model_type": getattr(model.config, "model_type", "unknown"),
                    "torch_available": True,
                },
            )
        except Exception as exc:
            loaded = LoadedModel(
                model_name=model_name,
                provider="mock",
                layer_count=32,
                hidden_size=2048,
                model=None,
                tokenizer=None,
                metadata={
                    "model_type": "mock-transformer",
                    "error": str(exc),
                },
            )
        self.current = loaded
        return loaded

    def get_metadata(self) -> dict[str, Any]:
        if self.current is None:
            return {
                "model_name": None,
                "loaded": False,
                "layer_count": 0,
                "provider": "none",
            }
        return {
            "model_name": self.current.model_name,
            "loaded": True,
            "layer_count": self.current.layer_count,
            "provider": self.current.provider,
            "hidden_size": self.current.hidden_size,
            **self.current.metadata,
        }

