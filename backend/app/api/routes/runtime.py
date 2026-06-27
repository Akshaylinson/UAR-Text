from __future__ import annotations

from fastapi import APIRouter, Depends

from ...runtime.runtime_controller import RuntimeController
from ...schemas.hardware import RuntimeStats

router = APIRouter(tags=["runtime"])


def get_runtime() -> RuntimeController:
    from ...main import runtime_controller

    return runtime_controller


@router.get("/api/runtime/stats", response_model=RuntimeStats)
def runtime_stats(runtime: RuntimeController = Depends(get_runtime)) -> dict:
    return runtime.runtime_stats()

