from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Universal AI Runtime")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = _env_int("PORT", 8000)
    model_name: str = os.getenv(
        "MODEL_NAME", "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    )
    max_active_layers: int = _env_int("MAX_ACTIVE_LAYERS", 4)
    cache_size: int = _env_int("CACHE_SIZE", 8)
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    )


settings = Settings()

