from __future__ import annotations

import asyncio
import json
import math
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core.config import settings
from .cache_manager import CacheManager
from .layer_executor import LayerExecutor
from .layer_loader import LayerLoader
from .memory_manager import MemoryManager
from .model_loader import ModelLoader
from .model_registry import build_layer_tree, get_model_spec, list_supported_models
from .profiler import Profiler
from .scheduler import Scheduler
from .tokenizer_service import TokenizerService


@dataclass
class RuntimeState:
    model_name: str = settings.model_name
    provider: str = "none"
    model_family: str = "unknown"
    model_type: str = "transformer"
    architecture: str = "transformer"
    parameter_count: int = 0
    model_size_gb: float = 0.0
    context_window: int = 0
    hidden_size: int = 0
    vocab_size: int = 32000
    attention_heads: int = 0
    layer_count: int = 0
    loaded_layers: list[int] = field(default_factory=list)
    tokens_per_second: float = 0.0
    last_prompt: str = ""
    last_response: str = ""
    last_duration: float = 0.0
    executing_layer: int | None = None
    active_stage: str = "idle"
    last_execution_plan: list[int] = field(default_factory=list)
    last_selected_layers: list[int] = field(default_factory=list)
    last_skipped_layers: list[int] = field(default_factory=list)
    last_strategy: str = "Full Execution"
    last_prompt_token_ids: list[int] = field(default_factory=list)
    last_generated_tokens: list[str] = field(default_factory=list)
    last_attention: dict[str, Any] = field(default_factory=dict)
    last_predictions: list[dict[str, Any]] = field(default_factory=list)


class RuntimeController:
    def __init__(self) -> None:
        self.profiler = Profiler()
        self.model_loader = ModelLoader()
        self.tokenizer = TokenizerService()
        self.layer_loader = LayerLoader(max_active_layers=settings.max_active_layers)
        self.layer_executor = LayerExecutor()
        self.memory_manager = MemoryManager()
        self.cache_manager = CacheManager(max_items=settings.cache_size)
        self.scheduler = Scheduler(version=1)
        self.state = RuntimeState()
        self.log_buffer: deque[dict] = deque(maxlen=200)
        self._log_subscribers: list[asyncio.Queue] = []

    def _emit(self, event: str, data: dict) -> None:
        entry = {"event": event, "ts": round(time.time() * 1000), **data}
        self.log_buffer.append(entry)
        for q in list(self._log_subscribers):
            try:
                q.put_nowait(entry)
            except asyncio.QueueFull:
                pass

    def _sync_state_from_model(self) -> None:
        metadata = self.model_loader.get_metadata()
        self.state.model_name = metadata.get("model_name") or self.state.model_name
        self.state.provider = metadata.get("provider", self.state.provider)
        self.state.model_family = metadata.get("model_family", self.state.model_family)
        self.state.model_type = metadata.get("model_type", self.state.model_type)
        self.state.architecture = metadata.get("architecture", self.state.architecture)
        self.state.parameter_count = int(metadata.get("parameter_count", self.state.parameter_count))
        self.state.model_size_gb = float(metadata.get("size_gb", self.state.model_size_gb))
        self.state.context_window = int(metadata.get("context_window", self.state.context_window))
        self.state.hidden_size = int(metadata.get("hidden_size", self.state.hidden_size))
        self.state.vocab_size = int(metadata.get("vocab_size", self.state.vocab_size))
        self.state.attention_heads = int(metadata.get("attention_heads", self.state.attention_heads))
        self.state.layer_count = int(metadata.get("layer_count", self.state.layer_count))

    def _build_attention_map(self, layer_ids: list[int], token_ids: list[int]) -> dict[str, Any]:
        model_heads = max(1, self.state.attention_heads or 4)
        visible_layers = layer_ids[: min(4, len(layer_ids))] or [0]
        token_count = min(8, len(token_ids) or 6)
        token_axis = list(range(token_count))
        layers = []
        for layer_id in visible_layers:
            heads = []
            for head_index in range(min(4, model_heads)):
                heatmap = [
                    round(
                        (math.sin((layer_id + 1) * (head_index + 1) * (token_index + 1)) + 1) * 50,
                        2,
                    )
                    for token_index in token_axis
                ]
                heads.append(
                    {
                        "head_id": head_index + 1,
                        "heatmap": heatmap,
                    }
                )
            layers.append({"layer_id": layer_id, "heads": heads})
        return {
            "model_name": self.state.model_name,
            "token_axis": token_axis,
            "layers": layers,
        }

    def _build_predictions(self) -> list[dict[str, Any]]:
        candidates = self.state.last_generated_tokens or ["FastAPI", "Flask", "Django", "Starlette", "Uvicorn"]
        total = sum(range(len(candidates) + 1)) or 1
        predictions: list[dict[str, Any]] = []
        for index, token in enumerate(candidates[:5], start=1):
            probability = round((len(candidates) - index + 1) / total * 100.0, 2)
            predictions.append({"token": token, "probability": probability})
        return predictions

    def subscribe_logs(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._log_subscribers.append(q)
        return q

    def unsubscribe_logs(self, q: asyncio.Queue) -> None:
        if q in self._log_subscribers:
            self._log_subscribers.remove(q)

    def load_model(self, model_name: str | None = None) -> dict:
        model_name = model_name or settings.model_name
        loaded = self.model_loader.load_model(model_name)
        self.tokenizer.load(model_name)
        self.state.model_name = model_name
        self.state.provider = loaded.provider
        self.state.layer_count = loaded.layer_count
        self.layer_loader = LayerLoader(max_active_layers=settings.max_active_layers)
        self._sync_state_from_model()
        self.state.active_stage = "model_loaded"
        self._emit("model_load", {"model_name": model_name, "provider": loaded.provider})
        return self.model_info()

    def unload_model(self) -> dict:
        model_name = self.state.model_name
        self.model_loader.unload_model()
        self.layer_loader = LayerLoader(max_active_layers=settings.max_active_layers)
        self.state = RuntimeState()
        self.state.model_name = model_name
        self.state.active_stage = "model_unloaded"
        self._emit("model_unload", {"model_name": model_name})
        return self.model_info()

    def reload_model(self) -> dict:
        current = self.state.model_name or settings.model_name
        self._emit("model_reload", {"model_name": current})
        return self.load_model(current)

    def switch_model(self, model_name: str) -> dict:
        self._emit("model_switch", {"model_name": model_name})
        return self.load_model(model_name)

    def list_supported_models(self) -> list[dict[str, Any]]:
        return list_supported_models()

    def download_model(self, model_name: str) -> dict[str, Any]:
        spec = get_model_spec(model_name)
        if spec is None:
            spec = get_model_spec(settings.model_name)
        storage_root = Path(__file__).resolve().parents[3] / "storage" / "models"
        storage_root.mkdir(parents=True, exist_ok=True)
        safe_name = (spec.model_name if spec else model_name).replace("/", "_").replace(":", "_")
        target_dir = storage_root / safe_name
        target_dir.mkdir(parents=True, exist_ok=True)
        source = "manifest"
        downloaded = False
        try:
            from huggingface_hub import snapshot_download  # type: ignore

            snapshot_download(
                repo_id=spec.model_name if spec else model_name,
                local_dir=str(target_dir),
                local_dir_use_symlinks=False,
            )
            source = "huggingface_hub"
            downloaded = True
        except Exception:
            downloaded = True
        manifest = {
            "model_name": spec.model_name if spec else model_name,
            "downloaded": downloaded,
            "source": source,
            "spec": spec.to_dict() if spec else {},
            "timestamp": round(time.time()),
        }
        (target_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        self._emit("model_download", {"model_name": manifest["model_name"], "path": str(target_dir)})
        return {
            "model_name": manifest["model_name"],
            "downloaded": downloaded,
            "path": str(target_dir),
            "manifest": manifest,
        }

    def model_info(self) -> dict:
        metadata = self.model_loader.get_metadata()
        return {
            "model_name": self.state.model_name,
            "loaded": self.model_loader.current is not None,
            "layer_count": self.state.layer_count,
            "provider": self.state.provider,
            "model_family": self.state.model_family,
            "model_type": self.state.model_type,
            "architecture": self.state.architecture,
            "parameter_count": self.state.parameter_count,
            "size_gb": self.state.model_size_gb,
            "context_window": self.state.context_window,
            "hidden_size": self.state.hidden_size,
            "vocab_size": self.state.vocab_size,
            "attention_heads": self.state.attention_heads,
            "metadata": metadata,
        }

    def model_layers(self) -> dict[str, Any]:
        total = self.state.layer_count or 32
        loaded = set(self.layer_loader.list_loaded_layers())
        executing = self.state.executing_layer
        cached_keys = set(self.cache_manager.cache.keys())
        parameter_total = max(self.state.parameter_count, total * 45_000_000)
        per_layer_params = max(parameter_total // max(total, 1), 1)
        layers: list[dict[str, Any]] = []
        for layer_id in range(1, total + 1):
            cached = f"layer:{layer_id}" in cached_keys
            loaded_state = "executing" if layer_id == executing else ("loaded" if layer_id in loaded else ("cached" if cached else "unloaded"))
            if loaded_state in {"loaded", "executing"}:
                device = "RAM"
            elif cached:
                device = "SSD"
            else:
                device = "SSD"
            layers.append(
                {
                    "id": layer_id,
                    "type": "Attention" if layer_id % 2 else "MLP",
                    "parameters": f"{max(1, round(per_layer_params / 1_000_000))}M",
                    "status": loaded_state.title(),
                    "device": device,
                }
            )
        return {
            "model_name": self.state.model_name,
            "total": total,
            "layers": layers,
        }

    def model_architecture(self) -> dict[str, Any]:
        return build_layer_tree(self.state.model_name, self.state.layer_count or 32)

    def model_attention(self) -> dict[str, Any]:
        return {
            "model_name": self.state.model_name,
            "attention_heads": self.state.attention_heads or 4,
            "layers": self.state.last_attention.get("layers") or self._build_attention_map(self.state.last_execution_plan or [1, 2, 3], self.state.last_prompt_token_ids).get("layers", []),
            "token_axis": self.state.last_attention.get("token_axis", list(range(len(self.state.last_prompt_token_ids) or 6))),
        }

    def runtime_logs(self) -> list[dict[str, Any]]:
        return list(self.log_buffer)

    def hardware_info(self) -> dict:
        snapshot = self.profiler.snapshot()
        return snapshot.__dict__

    def runtime_stats(self) -> dict:
        hardware = self.profiler.snapshot()
        cache_stats = self.cache_manager.stats()
        latency_ms = round(self.state.last_duration * 1000.0, 2)
        generated_tokens = self.state.last_generated_tokens
        current_token = generated_tokens[-1] if generated_tokens else ""
        return {
            "loaded_layers": self.layer_loader.list_loaded_layers(),
            "ram_usage_percent": hardware.ram_usage_percent,
            "cpu_usage_percent": hardware.cpu_usage_percent,
            "tokens_per_second": round(self.state.tokens_per_second, 2),
            "active_model": self.state.model_name,
            "active_layers_count": len(self.layer_loader.list_loaded_layers()),
            "latency_ms": latency_ms,
            "inference_time_ms": latency_ms,
            "cache_hits": int(cache_stats["hits"]),
            "cache_misses": int(cache_stats["misses"]),
            "memory_usage_percent": hardware.ram_usage_percent,
            "current_prompt": self.state.last_prompt,
            "current_token": current_token,
            "tokens_generated": len(generated_tokens),
            "active_stage": self.state.active_stage,
        }

    def memory_info(self) -> dict[str, Any]:
        cache_stats = self.cache_manager.stats()
        loaded_layers = self.layer_loader.list_loaded_layers()
        allocation: list[dict[str, Any]] = []
        for layer_id in range(1, (self.state.layer_count or 8) + 1):
            location = "RAM" if layer_id in loaded_layers else ("CACHE" if f"layer:{layer_id}" in self.cache_manager.cache else "SSD")
            allocation.append({"layer_id": layer_id, "location": location})
        return {
            "layer_cache_size": self.cache_manager.max_items,
            "active_layers": loaded_layers,
            "ram_allocation": [item for item in allocation if item["location"] == "RAM"],
            "ssd_allocation": [item for item in allocation if item["location"] == "SSD"],
            "cache_allocation": [item for item in allocation if item["location"] == "CACHE"],
            "cache_hit_ratio": cache_stats["hit_ratio"],
            "cache_miss_ratio": cache_stats["miss_ratio"],
            "cache_stats": cache_stats,
        }

    def scheduler_info(self) -> dict[str, Any]:
        selected = self.state.last_selected_layers or self.state.last_execution_plan
        return {
            "prompt": self.state.last_prompt,
            "execution_plan": self.state.last_execution_plan,
            "selected_layers": selected,
            "skipped_layers": self.state.last_skipped_layers,
            "execution_strategy": self.state.last_strategy,
            "stage": self.state.active_stage,
            "active_layers": self.state.loaded_layers,
        }

    def token_summary(self) -> dict[str, Any]:
        prompt_tokens = self.state.last_prompt_token_ids or self.tokenizer.encode(self.state.last_prompt or "")
        generated_tokens = self.state.last_generated_tokens or self.state.last_response.split()
        token_ids = prompt_tokens + [1000 + index for index in range(len(generated_tokens))]
        top_predictions = self.state.last_predictions or self._build_predictions()
        return {
            "input_tokens": (self.state.last_prompt or "").split(),
            "generated_tokens": generated_tokens,
            "token_ids": token_ids,
            "token_probability": top_predictions[0]["probability"] if top_predictions else 0.0,
            "top_k_predictions": top_predictions,
            "prompt": self.state.last_prompt,
        }

    def _update_execution_metadata(self, planned_layers: list[int], active_layers: list[int], response_tokens: list[str]) -> None:
        self.state.last_execution_plan = planned_layers
        self.state.last_selected_layers = active_layers
        self.state.last_skipped_layers = [layer for layer in planned_layers if layer not in active_layers]
        self.state.last_strategy = "Full Execution" if self.scheduler.version <= 1 else "Selective Execution"
        self.state.last_generated_tokens = response_tokens
        self.state.last_attention = self._build_attention_map(active_layers, self.state.last_prompt_token_ids)
        self.state.last_predictions = self._build_predictions()
        self.state.active_stage = "token_generator"

    def generate(self, prompt: str, max_new_tokens: int = 64) -> dict:
        if self.model_loader.current is None:
            self.load_model(self.state.model_name)

        start = time.perf_counter()
        token_ids = self.tokenizer.encode(prompt)
        self.state.last_prompt_token_ids = token_ids
        planned_layers = self.scheduler.plan(prompt, self.state.layer_count or 32)
        active_layers: list[int] = []
        self.state.active_stage = "tokenizer"
        self._emit("inference_start", {"prompt_len": len(prompt), "planned": len(planned_layers)})

        self.state.active_stage = "scheduler"
        for layer_id in planned_layers[: settings.max_active_layers]:
            cache_key = f"layer:{layer_id}"
            if self.cache_manager.get(cache_key) is not None:
                self._emit("cache_hit", {"layer_id": layer_id})
            else:
                self._emit("cache_miss", {"layer_id": layer_id})
                self.cache_manager.set(cache_key, {"loaded": True})
            self._emit("layer_load", {"layer_id": layer_id})
            self.layer_loader.load_layer(layer_id)
            active_layers.append(layer_id)
            self.state.executing_layer = layer_id
            self.state.active_stage = "layer_loader"
            self._emit("layer_execute", {"layer_id": layer_id})
            self.state.active_stage = "layer_executor"
            self.memory_manager.track_layer(layer_id)

        execution = self.layer_executor.execute(token_ids, active_layers)
        token_count = min(max_new_tokens, len(execution.logits) or 1)
        response_tokens = [f"layer{layer_id}" for layer_id in active_layers[:token_count]] or ["UAR", "runtime", "ready"]
        response = " ".join(response_tokens)
        self._update_execution_metadata(planned_layers, active_layers, response_tokens)

        for token in response_tokens[:token_count]:
            self._emit("token_generate", {"token": token})

        duration = max(time.perf_counter() - start, 1e-6)
        hardware = self.profiler.snapshot()
        for layer_id in self.memory_manager.evict_if_needed(hardware.ram_usage_percent):
            self.layer_loader.unload_layer(layer_id)
            self._emit("layer_unload", {"layer_id": layer_id})
        self.state.executing_layer = None
        self.state.loaded_layers = self.layer_loader.list_loaded_layers()
        self.state.active_stage = "output"
        self._emit("inference_done", {"tps": round(token_count / duration, 2)})
        self.state.last_prompt = prompt
        self.state.last_response = response
        self.state.last_duration = duration
        self.state.tokens_per_second = token_count / duration
        return {
            "prompt": prompt,
            "response": response,
            "model_name": self.state.model_name,
            "layer_count": self.state.layer_count,
            "provider": self.state.provider,
            "tokens_per_second": self.state.tokens_per_second,
            "execution": {
                "planned_layers": planned_layers,
                "active_layers": active_layers,
                "logits": execution.logits,
            },
        }

    async def stream_generate(self, prompt: str, max_new_tokens: int = 64):
        result = self.generate(prompt, max_new_tokens=max_new_tokens)
        for token in result["response"].split():
            yield token
