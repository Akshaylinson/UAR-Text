from __future__ import annotations

from fastapi import APIRouter, Depends

from ...runtime.runtime_controller import RuntimeController
from ...schemas.inference import GenerateRequest, GenerateResponse

router = APIRouter(tags=["inference"])


def get_runtime() -> RuntimeController:
    from ...main import runtime_controller

    return runtime_controller


@router.post("/api/generate", response_model=GenerateResponse)
def generate(
    request: GenerateRequest, runtime: RuntimeController = Depends(get_runtime)
) -> dict:
    return runtime.generate(request.prompt, max_new_tokens=request.max_new_tokens)

