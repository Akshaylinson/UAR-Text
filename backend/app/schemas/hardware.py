from __future__ import annotations

from pydantic import BaseModel, Field


class HardwareInfo(BaseModel):
    cpu: str = Field(default="unknown")
    cpu_cores: int = Field(default=0)
    cpu_threads: int = Field(default=0)
    cpu_usage_percent: float = Field(default=0.0)
    ram_total_gb: float = Field(default=0.0)
    ram_used_gb: float = Field(default=0.0)
    ram_free_gb: float = Field(default=0.0)
    ram_usage_percent: float = Field(default=0.0)
    disk_total_gb: float = Field(default=0.0)
    disk_used_gb: float = Field(default=0.0)
    disk_free_gb: float = Field(default=0.0)
    disk_usage_percent: float = Field(default=0.0)
    gpu_available: bool = Field(default=False)
    gpu_memory_gb: float = Field(default=0.0)


class RuntimeStats(BaseModel):
    loaded_layers: list[int]
    ram_usage_percent: float
    cpu_usage_percent: float
    tokens_per_second: float
    active_model: str
    active_layers_count: int
    latency_ms: float = 0.0
    inference_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    memory_usage_percent: float = 0.0
