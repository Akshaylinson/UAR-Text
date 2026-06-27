from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)
    max_new_tokens: int = Field(default=64, ge=1, le=256)
    stream: bool = Field(default=False)


class GenerateResponse(BaseModel):
    prompt: str
    response: str
    model_name: str
    layer_count: int
    provider: str

