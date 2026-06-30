



from __future__ import annotations

import json

from fastapi import WebSocket, WebSocketDisconnect

from ..runtime.runtime_controller import RuntimeController


async def chat_stream(websocket: WebSocket, runtime: RuntimeController) -> None:
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_text()
            try:
                data = json.loads(payload)
                prompt = data.get("prompt", "")
                max_new_tokens = int(data.get("max_new_tokens", 64))
            except json.JSONDecodeError:
                prompt = payload
                max_new_tokens = 64

            async for token in runtime.stream_generate(
                prompt, max_new_tokens=max_new_tokens
            ):
                await websocket.send_json({"type": "token", "value": token})
            await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        return


