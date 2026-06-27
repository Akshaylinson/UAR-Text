from __future__ import annotations

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from .api.routes.health import router as health_router
from .api.routes.hardware import router as hardware_router
from .api.routes.inference import router as inference_router
from .api.routes.model import router as model_router
from .api.routes.runtime import router as runtime_router
from .core.config import settings
from .core.logger import configure_logging
from .runtime.runtime_controller import RuntimeController
from .websocket.stream import chat_stream

configure_logging()

runtime_controller = RuntimeController()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in settings.cors_origins else list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(hardware_router)
app.include_router(model_router)
app.include_router(inference_router)
app.include_router(runtime_router)


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    await chat_stream(websocket, runtime_controller)

