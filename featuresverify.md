Feature Verification Checklist

Below is the complete feature list that should exist in the final V1.

MODULE 1 — Model Management
Features
 Load model from Hugging Face
 Unload model
 Reload model
 View model information
 Download model
 List supported models
 Switch active model
 View model size
 View parameter count

Dashboard:

Active Model:
TinyLlama-1.1B

Model Size:
2.2 GB

Parameters:
1.1 Billion

Architecture:
Decoder Transformer

Layers:
22

Vocabulary Size:
32000
MODULE 2 — LLM Architecture Explorer

This is currently missing and should definitely be implemented.

Dashboard Page
/pages/model-explorer

Purpose:

Allow admin to understand the complete internal architecture of the loaded LLM.

Display
Basic Information
Model Name
Model Family
Model Type
Architecture
Parameter Count
Model Size
Context Window
Hidden Size
Vocabulary Size
Layer Tree

Example:

TinyLlama
│
├── Embedding Layer
│
├── Transformer Block 1
│   ├── Input LayerNorm
│   ├── Self Attention
│   │   ├── Q Projection
│   │   ├── K Projection
│   │   ├── V Projection
│   │   └── Output Projection
│   │
│   ├── MLP
│   │   ├── Gate Projection
│   │   ├── Up Projection
│   │   └── Down Projection
│   │
│   └── Residual Connection
│
├── Transformer Block 2
│
├── ...
│
├── Transformer Block 22
│
└── LM Head

Display as expandable tree cards.

MODULE 3 — Layer Dashboard

New page:

/pages/layers

Display:

Layer	Type	Parameters	Status	Device
1	Attention	45M	Loaded	RAM
2	MLP	45M	Cached	SSD
3	Attention	45M	Executing	RAM
4	MLP	45M	Unloaded	SSD

Status colors:

Green → Loaded
Yellow → Executing
Blue → Cached
Gray → Unloaded
MODULE 4 — Runtime Dashboard

Page:

/pages/runtime

Display:

Runtime Status

Example:

Current Prompt

Current Token

Tokens Generated

Tokens/sec

Latency

Inference Time

Active Layers

Cache Hits

Cache Misses

Memory Usage

CPU Usage
Execution Pipeline Visualization

Show:

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
Output

Highlight currently active stage.

MODULE 5 — Hardware Dashboard

Page:

/pages/hardware

Display:

CPU Model

CPU Cores

CPU Threads

RAM Total

RAM Used

RAM Free

Disk Size

Disk Usage

GPU Available

GPU Memory

Realtime charts:

CPU Usage %

RAM Usage %

Disk I/O

Tokens/sec

Update every 2 seconds.

MODULE 6 — Scheduler Dashboard

Very important.

Page:

/pages/scheduler

Display:

Prompt

Execution Plan

Selected Layers

Skipped Layers

Execution Strategy

Example:

Prompt:
Write FastAPI API.

Strategy:
Full Execution

Layers Selected:
1-22

Layers Skipped:
None

Future:

Strategy:
Selective Execution
MODULE 7 — Memory Manager Dashboard

Page:

/pages/memory

Display:

Layer Cache Size

Active Layers

RAM Allocation

SSD Allocation

Cache Hit Ratio

Cache Miss Ratio

Example:

Layer 1 → RAM

Layer 2 → RAM

Layer 3 → SSD

Layer 4 → Cache
MODULE 8 — Token Visualization Dashboard

Page:

/pages/tokens

Display:

Input Tokens

Generated Tokens

Token IDs

Token Probability

Top-K Predictions

Example:

Token:
FastAPI

Probability:
92%

Top Predictions:

FastAPI → 92%

Flask → 3%

Django → 2%
MODULE 9 — Attention Visualization

Very important for understanding LLMs.

Page:

/pages/attention

Display:

Attention Heads

Attention Maps

Layer-wise Attention

Example:

Layer 5

Head 1

Head 2

Head 3

Heatmaps should be displayed.

MODULE 10 — Runtime Logs

Page:

/pages/logs

Realtime logs:

Loading Layer 1

Executing Layer 1

Unloading Layer 1

Cache Hit

Cache Miss

Generating Token
MODULE 11 — Metrics Dashboard

Page:

/pages/metrics

Charts:

Inference Latency

Tokens/sec

Memory Usage

CPU Usage

Layer Loading Time

Response Time
MODULE 12 — Model Inspector API

Required APIs:

GET /api/model/info

GET /api/model/layers

GET /api/model/architecture

GET /api/model/attention

GET /api/runtime/stats

GET /api/runtime/logs

GET /api/hardware

GET /api/memory

GET /api/scheduler
Final Dashboard Structure
Dashboard

├── Chat
├── Hardware
├── Runtime
├── Model Explorer
├── Layers
├── Scheduler
├── Memory
├── Tokens
├── Attention
├── Metrics
├── Logs
└── Settings
Features Already Implemented vs Missing
Likely Already Present
✓ Chat
✓ Model Loading
✓ Basic Inference
✓ FastAPI
✓ Docker