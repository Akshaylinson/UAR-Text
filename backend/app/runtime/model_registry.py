from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class ModelSpec:
    model_name: str
    model_family: str
    model_type: str
    architecture: str
    parameter_count: int
    size_gb: float
    context_window: int
    hidden_size: int
    vocab_size: int
    layer_count: int
    attention_heads: int
    source: str = "huggingface"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_MODEL_REGISTRY: list[ModelSpec] = [
    ModelSpec(
        model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        model_family="TinyLlama",
        model_type="decoder_transformer",
        architecture="Decoder Transformer",
        parameter_count=1_100_000_000,
        size_gb=2.2,
        context_window=2048,
        hidden_size=2048,
        vocab_size=32000,
        layer_count=22,
        attention_heads=32,
    ),
    ModelSpec(
        model_name="google/gemma-2b-it",
        model_family="Gemma",
        model_type="decoder_transformer",
        architecture="Decoder Transformer",
        parameter_count=2_000_000_000,
        size_gb=4.0,
        context_window=8192,
        hidden_size=2048,
        vocab_size=256000,
        layer_count=18,
        attention_heads=16,
    ),
    ModelSpec(
        model_name="meta-llama/Llama-3.2-3B-Instruct",
        model_family="Llama",
        model_type="decoder_transformer",
        architecture="Decoder Transformer",
        parameter_count=3_200_000_000,
        size_gb=6.4,
        context_window=8192,
        hidden_size=3072,
        vocab_size=128256,
        layer_count=28,
        attention_heads=24,
    ),
    ModelSpec(
        model_name="Qwen/Qwen2.5-3B-Instruct",
        model_family="Qwen",
        model_type="decoder_transformer",
        architecture="Decoder Transformer",
        parameter_count=3_000_000_000,
        size_gb=6.0,
        context_window=32768,
        hidden_size=3072,
        vocab_size=151936,
        layer_count=28,
        attention_heads=24,
    ),
    ModelSpec(
        model_name="mistralai/Mistral-7B-Instruct-v0.3",
        model_family="Mistral",
        model_type="decoder_transformer",
        architecture="Decoder Transformer",
        parameter_count=7_000_000_000,
        size_gb=14.0,
        context_window=32768,
        hidden_size=4096,
        vocab_size=32768,
        layer_count=32,
        attention_heads=32,
    ),
]


def _normalize(name: str) -> str:
    return name.strip().lower()


def list_supported_models() -> list[dict[str, Any]]:
    return [model.to_dict() for model in _MODEL_REGISTRY]


def get_model_spec(model_name: str | None) -> ModelSpec | None:
    if not model_name:
        return None
    normalized = _normalize(model_name)
    for model in _MODEL_REGISTRY:
        if normalized == _normalize(model.model_name):
            return model
    for model in _MODEL_REGISTRY:
        if normalized in _normalize(model.model_name):
            return model
    return None


def default_model_spec() -> ModelSpec:
    return _MODEL_REGISTRY[0]


def build_layer_tree(model_name: str, layer_count: int) -> dict[str, Any]:
    spec = get_model_spec(model_name) or default_model_spec()
    children: list[dict[str, Any]] = [
        {
            "label": "Embedding Layer",
            "type": "embedding",
            "children": [],
        }
    ]
    for layer_index in range(1, max(layer_count, 1) + 1):
        children.append(
            {
                "label": f"Transformer Block {layer_index}",
                "type": "block",
                "children": [
                    {
                        "label": "Input LayerNorm",
                        "type": "norm",
                        "children": [],
                    },
                    {
                        "label": "Self Attention",
                        "type": "attention",
                        "children": [
                            {"label": "Q Projection", "type": "projection", "children": []},
                            {"label": "K Projection", "type": "projection", "children": []},
                            {"label": "V Projection", "type": "projection", "children": []},
                            {"label": "Output Projection", "type": "projection", "children": []},
                        ],
                    },
                    {
                        "label": "MLP",
                        "type": "mlp",
                        "children": [
                            {"label": "Gate Projection", "type": "projection", "children": []},
                            {"label": "Up Projection", "type": "projection", "children": []},
                            {"label": "Down Projection", "type": "projection", "children": []},
                        ],
                    },
                    {
                        "label": "Residual Connection",
                        "type": "residual",
                        "children": [],
                    },
                ],
            }
        )
    children.append(
        {
            "label": "LM Head",
            "type": "lm_head",
            "children": [],
        }
    )
    return {
        "label": spec.model_family,
        "type": "root",
        "model_name": spec.model_name,
        "children": children,
    }
