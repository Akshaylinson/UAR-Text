from __future__ import annotations

from pydantic import BaseModel, Field


class ModelLoadRequest(BaseModel):
    model_name: str = Field(default="TinyLlama/TinyLlama-1.1B-Chat-v1.0")


class ModelInfo(BaseModel):
    model_name: str
    loaded: bool
    layer_count: int
    provider: str
    architecture: str = "transformer"
    vocab_size: int = 32000
    hidden_size: int = 0

