from __future__ import annotations

from pydantic import BaseModel, Field


class ModelLoadRequest(BaseModel):
    model_name: str = Field(default="TinyLlama/TinyLlama-1.1B-Chat-v1.0")


class ModelInfo(BaseModel):
    model_name: str
    loaded: bool
    layer_count: int
    provider: str
    model_family: str = "unknown"
    model_type: str = "transformer"
    architecture: str = "transformer"
    parameter_count: int = 0
    size_gb: float = 0.0
    context_window: int = 0
    hidden_size: int = 0
    vocab_size: int = 32000
    attention_heads: int = 0
