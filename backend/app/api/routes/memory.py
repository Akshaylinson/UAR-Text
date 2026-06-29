from __future__ import annotations

from fastapi import APIRouter, Depends

from ...runtime.runtime_controller import RuntimeController

router = APIRouter(tags=["memory"])


def get_runtime() -> RuntimeController:
    from ...main import runtime_controller

    return runtime_controller


@router.get("/api/memory")
def memory(runtime: RuntimeController = Depends(get_runtime)) -> dict:
    return runtime.memory_info()
