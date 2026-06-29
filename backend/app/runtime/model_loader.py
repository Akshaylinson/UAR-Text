from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .model_registry import default_model_spec, get_model_spec


@dataclass
class LoadedModel:
    model_name: str
    provider: str
    layer_count: int
    hidden_size: int
    model_size_gb: float
    parameter_count: int
    context_window: int
    vocab_size: int
    attention_heads: int
    model: Any = None
    tokenizer: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelLoader:
    def __init__(self) -> None:
        self.current: LoadedModel | None = None

    def load_model(self, model_name: str) -> LoadedModel:
        spec = get_model_spec(model_name) or default_model_spec()
        metadata: dict[str, Any] = {
            "model_family": spec.model_family,
            "model_type": spec.model_type,
            "architecture": spec.architecture,
            "parameter_count": spec.parameter_count,
            "size_gb": spec.size_gb,
            "context_window": spec.context_window,
            "hidden_size": spec.hidden_size,
            "vocab_size": spec.vocab_size,
            "layer_count": spec.layer_count,
            "attention_heads": spec.attention_heads,
            "source": spec.source,
        }
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
            layer_count = len(getattr(layers, "layers", [])) if layers else spec.layer_count
            hidden_size = int(getattr(model.config, "hidden_size", spec.hidden_size))
            parameter_count = int(sum(parameter.numel() for parameter in model.parameters()))
            loaded = LoadedModel(
                model_name=model_name,
                provider="transformers",
                layer_count=layer_count,
                hidden_size=hidden_size,
                model_size_gb=round(parameter_count * 4 / (1024**3), 2),
                parameter_count=parameter_count,
                context_window=int(getattr(model.config, "max_position_embeddings", spec.context_window)),
                vocab_size=int(getattr(model.config, "vocab_size", spec.vocab_size)),
                attention_heads=int(getattr(model.config, "num_attention_heads", spec.attention_heads)),
                model=model,
                tokenizer=tokenizer,
                metadata={
                    **metadata,
                    "model_type": getattr(model.config, "model_type", spec.model_type),
                    "torch_available": True,
                },
            )
        except Exception as exc:
            loaded = LoadedModel(
                model_name=model_name,
                provider="mock",
                layer_count=spec.layer_count,
                hidden_size=spec.hidden_size,
                model_size_gb=spec.size_gb,
                parameter_count=spec.parameter_count,
                context_window=spec.context_window,
                vocab_size=spec.vocab_size,
                attention_heads=spec.attention_heads,
                model=None,
                tokenizer=None,
                metadata={
                    **metadata,
                    "model_type": spec.model_type,
                    "error": str(exc),
                },
            )
        self.current = loaded
        return loaded

    def unload_model(self) -> None:
        self.current = None

    def get_metadata(self) -> dict[str, Any]:
        if self.current is None:
            spec = default_model_spec()
            return {
                "model_name": None,
                "loaded": False,
                "layer_count": 0,
                "provider": "none",
                "model_family": spec.model_family,
                "model_type": spec.model_type,
                "architecture": spec.architecture,
                "parameter_count": spec.parameter_count,
                "size_gb": spec.size_gb,
                "context_window": spec.context_window,
                "hidden_size": spec.hidden_size,
                "vocab_size": spec.vocab_size,
                "attention_heads": spec.attention_heads,
            }
        return {
            "model_name": self.current.model_name,
            "loaded": True,
            "layer_count": self.current.layer_count,
            "provider": self.current.provider,
            "model_family": self.current.metadata.get("model_family", "unknown"),
            "model_type": self.current.metadata.get("model_type", "transformer"),
            "architecture": self.current.metadata.get("architecture", "Decoder Transformer"),
            "parameter_count": self.current.parameter_count,
            "size_gb": self.current.model_size_gb,
            "context_window": self.current.context_window,
            "hidden_size": self.current.hidden_size,
            "vocab_size": self.current.vocab_size,
            "attention_heads": self.current.attention_heads,
            **self.current.metadata,
        }
