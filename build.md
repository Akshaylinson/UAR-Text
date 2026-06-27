# Project Specification: Universal AI Runtime (UAR) v1

## Project Overview

Build a full-stack AI runtime platform named **Universal AI Runtime (UAR)**.

The goal of the project is to create a hardware-aware runtime capable of executing Transformer-based text LLMs efficiently on low-resource hardware through dynamic layer loading, memory management, hardware profiling, and runtime orchestration.

The first supported model will be:

* TinyLlama/TinyLlama-1.1B-Chat-v1.0

The architecture must be designed so that future support for:

* Gemma
* Llama
* Qwen
* Mistral

can be easily added.

The entire project must run using Docker and Docker Compose.

---

# Core Objectives

Version 1 must support:

1. Load TinyLlama model.
2. Execute inference.
3. Execute model layer-by-layer.
4. Dynamically load and unload layers.
5. Profile hardware resources.
6. Monitor RAM usage.
7. Provide REST APIs.
8. Provide WebSocket streaming.
9. Provide a real-time dashboard.
10. Provide Docker deployment.

---

# Tech Stack

## Backend

* Python 3.12
* FastAPI
* Uvicorn
* Pydantic v2
* HuggingFace Transformers
* PyTorch
* Accelerate
* Safetensors
* Psutil
* Loguru

## Frontend

* HTML5
* Tailwind CSS
* Vanilla JavaScript
* HTMX (optional)

## Realtime

* FastAPI WebSockets

## Storage

* Local filesystem

## Deployment

* Docker
* Docker Compose

---

# Project Structure

```text
universal-runtime/

├── backend/
│
│   ├── app/
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── hardware.py
│   │   │   ├── model.py
│   │   │   ├── inference.py
│   │   │   └── runtime.py
│   │
│   ├── websocket/
│   │   └── stream.py
│   │
│   ├── runtime/
│   │   ├── runtime_controller.py
│   │   ├── scheduler.py
│   │   ├── model_loader.py
│   │   ├── layer_loader.py
│   │   ├── layer_executor.py
│   │   ├── memory_manager.py
│   │   ├── cache_manager.py
│   │   ├── profiler.py
│   │   └── tokenizer_service.py
│   │
│   ├── services/
│   │   ├── hardware_service.py
│   │   ├── inference_service.py
│   │   └── monitoring_service.py
│   │
│   ├── schemas/
│   │   ├── inference.py
│   │   ├── hardware.py
│   │   └── model.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── logger.py
│   │
│   ├── main.py
│   │
│   └── requirements.txt
│
├── frontend/
│
│   ├── index.html
│   ├── dashboard.html
│   ├── runtime.html
│   ├── chat.html
│   │
│   ├── js/
│   ├── css/
│   └── assets/
│
├── storage/
│
│   ├── models/
│   ├── cache/
│   └── metadata/
│
├── docker/
│
│   ├── backend.Dockerfile
│   └── nginx.Dockerfile
│
├── docker-compose.yml
├── .env
├── README.md
└── Makefile
```

---

# Backend Features

## Hardware Profiler

Create a service that automatically detects:

* CPU model
* Number of cores
* Total RAM
* Available RAM
* GPU availability
* Disk size

Expose API:

```http
GET /api/hardware
```

Example response:

```json
{
    "cpu":"Intel i5",
    "cores":12,
    "ram_total_gb":16,
    "ram_free_gb":8.2,
    "gpu_available":false
}
```

---

## Model Loader

Load TinyLlama model from Hugging Face.

Use:

```python
TinyLlama/TinyLlama-1.1B-Chat-v1.0
```

Requirements:

* Lazy loading support.
* Layer access support.
* Return model metadata.

Expose:

```http
POST /api/model/load
```

---

## Layer Loader

Must support:

```python
load_layer(layer_id)

unload_layer(layer_id)

preload_next_layer(layer_id)
```

Use LRU caching.

Only keep a configurable number of layers in memory.

Default:

```python
MAX_ACTIVE_LAYERS=4
```

---

## Layer Executor

Implement manual execution:

```python
hidden = embeddings(tokens)

for layer in active_layers:
    hidden = layer(hidden)

logits = lm_head(hidden)
```

The runtime must support:

* Full model execution.
* Layer-by-layer execution.

---

## Scheduler

Version 1:

Always execute all layers.

Version 2:

Prompt-aware execution.

Architecture:

```text
Prompt
↓
Intent Detector
↓
Execution Plan
↓
Layer Schedule
```

---

## Runtime Controller

Responsible for orchestrating:

* Tokenization
* Layer loading
* Layer execution
* Layer unloading
* Caching
* Generation

Pipeline:

```text
Prompt
↓
Tokenizer
↓
Scheduler
↓
Layer Loader
↓
Layer Executor
↓
Token Generator
↓
Response
```

---

# Monitoring APIs

Create:

```http
GET /api/runtime/stats
```

Return:

```json
{
    "loaded_layers":[1,2,3],
    "ram_usage_percent":48,
    "cpu_usage_percent":32,
    "tokens_per_second":4,
    "active_model":"TinyLlama"
}
```

---

# Frontend Pages

## Dashboard

Display:

* CPU usage
* RAM usage
* Active layers
* Tokens/sec
* Model information

Use polling every 3 seconds.

---

## Runtime Viewer

Visualize:

```text
Layer 1 : Loaded
Layer 2 : Executing
Layer 3 : Cached
Layer 4 : Unloaded
```

Display as cards.

---

## Chat UI

Create ChatGPT-like interface.

Features:

* Streaming responses
* Chat history
* Clear chat

Use WebSockets.

---

# REST APIs

```http
GET /api/health

GET /api/hardware

POST /api/model/load

GET /api/model/info

POST /api/generate

GET /api/runtime/stats
```

---

# WebSocket

```text
/ws/chat
```

Support token streaming.

---

# Docker Requirements

Create:

## backend.Dockerfile

Requirements:

* Python 3.12
* PyTorch CPU build
* Transformers
* Uvicorn

Expose:

```text
8000
```

---

## Nginx Container

Serve frontend.

Expose:

```text
80
```

---

# docker-compose.yml

Services:

```yaml
backend
frontend
```

Volumes:

```yaml
./storage:/app/storage
```

Environment variables:

```yaml
MODEL_NAME=TinyLlama/TinyLlama-1.1B-Chat-v1.0
MAX_ACTIVE_LAYERS=4
CACHE_SIZE=8
LOG_LEVEL=INFO
```

---

# Future Roadmap

Version 2:

* Gemma support
* Qwen support
* Mistral support
* Quantization support
* GGUF support

Version 3:

* Prompt-aware layer execution
* Dynamic quantization
* Hardware-aware scheduling

Version 4:

* Automatic expert discovery
* Modular execution

Version 5:

* Universal Transformer Runtime

```
```
