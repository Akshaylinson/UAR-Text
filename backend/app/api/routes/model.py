from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.config import settings
from ...runtime.runtime_controller import RuntimeController
from ...schemas.model import ModelInfo, ModelLoadRequest

router = APIRouter(tags=["model"])


def get_runtime() -> RuntimeController:
    from ...main import runtime_controller

    return runtime_controller


@router.post("/api/model/load", response_model=ModelInfo)
def load_model(
    request: ModelLoadRequest, runtime: RuntimeController = Depends(get_runtime)
) -> dict:
    return runtime.load_model(request.model_name)


@router.get("/api/model/info", response_model=ModelInfo)
def model_info(runtime: RuntimeController = Depends(get_runtime)) -> dict:
    info = runtime.model_info()
    metadata = info.get("metadata", {})
    return {
        "model_name": info["model_name"],
        "loaded": info["loaded"],
        "layer_count": info["layer_count"],
        "provider": info["provider"],
        "architecture": metadata.get("model_type", "transformer"),
        "vocab_size": metadata.get("vocab_size", 32000),
        "hidden_size": metadata.get("hidden_size", 0),
    }

