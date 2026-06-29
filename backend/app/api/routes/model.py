from __future__ import annotations

from fastapi import APIRouter, Depends

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


@router.post("/api/model/switch", response_model=ModelInfo)
def switch_model(
    request: ModelLoadRequest, runtime: RuntimeController = Depends(get_runtime)
) -> dict:
    return runtime.switch_model(request.model_name)


@router.post("/api/model/unload")
def unload_model(runtime: RuntimeController = Depends(get_runtime)) -> dict:
    return runtime.unload_model()


@router.post("/api/model/reload", response_model=ModelInfo)
def reload_model(runtime: RuntimeController = Depends(get_runtime)) -> dict:
    return runtime.reload_model()


@router.post("/api/model/download")
def download_model(
    request: ModelLoadRequest, runtime: RuntimeController = Depends(get_runtime)
) -> dict:
    return runtime.download_model(request.model_name)


@router.get("/api/model/list")
def list_models(runtime: RuntimeController = Depends(get_runtime)) -> dict:
    return {"models": runtime.list_supported_models()}


@router.get("/api/model/info", response_model=ModelInfo)
def model_info(runtime: RuntimeController = Depends(get_runtime)) -> dict:
    return runtime.model_info()


@router.get("/api/model/layers")
def model_layers(runtime: RuntimeController = Depends(get_runtime)) -> dict:
    return runtime.model_layers()


@router.get("/api/model/architecture")
def model_architecture(runtime: RuntimeController = Depends(get_runtime)) -> dict:
    return runtime.model_architecture()


@router.get("/api/model/attention")
def model_attention(runtime: RuntimeController = Depends(get_runtime)) -> dict:
    return runtime.model_attention()
