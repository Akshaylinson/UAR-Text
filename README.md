# Universal AI Runtime

UAR is a FastAPI-based runtime scaffold for layer-aware LLM execution.
Page	URL
Dashboard	http://128.30.9.8:8000/ui/dashboard.html
Chat	http://128.30.9.8:8000/ui/chat.html
Runtime	http://128.30.9.8:8000/ui/runtime.html
Root (redirects to index)	http://128.30.9.8:8000/
API Docs	http://128.30.9.8:8000/docs

## What is included

- Backend API for health, hardware, model, inference, and runtime stats
- WebSocket chat streaming endpoint
- Static frontend dashboard, runtime viewer, and chat UI
- Docker and Docker Compose files
- A lightweight fallback runtime so the project can run without heavy model downloads

## Run locally

```bash
uvicorn backend.app.main:app --reload
```

## Run with Docker

```bash
docker compose up --build
```

