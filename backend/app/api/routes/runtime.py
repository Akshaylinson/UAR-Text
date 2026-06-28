from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from ...runtime.runtime_controller import RuntimeController
from ...schemas.hardware import RuntimeStats

router = APIRouter(tags=["runtime"])


def get_runtime() -> RuntimeController:
    from ...main import runtime_controller
    return runtime_controller


@router.get("/api/runtime/stats", response_model=RuntimeStats)
def runtime_stats(runtime: RuntimeController = Depends(get_runtime)) -> dict:
    return runtime.runtime_stats()


@router.get("/api/runtime/layers")
def runtime_layers(runtime: RuntimeController = Depends(get_runtime)) -> dict:
    loaded = set(runtime.layer_loader.list_loaded_layers())
    total = runtime.state.layer_count or 32
    executing = runtime.state.executing_layer
    return {
        "total": total,
        "max_active": runtime.layer_loader.max_active_layers,
        "layers": [
            {
                "id": i,
                "state": "executing" if i == executing else ("loaded" if i in loaded else "unloaded"),
            }
            for i in range(total)
        ],
    }


@router.websocket("/ws/logs")
async def log_stream(websocket: WebSocket, runtime: RuntimeController = Depends(get_runtime)) -> None:
    await websocket.accept()
    q = runtime.subscribe_logs()
    # send buffered history first
    for entry in list(runtime.log_buffer):
        await websocket.send_json(entry)
    try:
        while True:
            entry = await q.get()
            await websocket.send_json(entry)
    except (WebSocketDisconnect, Exception):
        runtime.unsubscribe_logs(q)

