from __future__ import annotations

from pydantic import BaseModel, Field


class HardwareInfo(BaseModel):
    cpu: str = Field(default="unknown")
    cores: int = Field(default=0)
    ram_total_gb: float = Field(default=0.0)
    ram_free_gb: float = Field(default=0.0)
    gpu_available: bool = Field(default=False)
    disk_total_gb: float = Field(default=0.0)
    disk_free_gb: float = Field(default=0.0)


class RuntimeStats(BaseModel):
    loaded_layers: list[int]
    ram_usage_percent: float
    cpu_usage_percent: float
    tokens_per_second: float
    active_model: str
    active_layers_count: int

