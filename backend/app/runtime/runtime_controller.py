from __future__ import annotations

import time
from dataclasses import dataclass, field

from ..core.config import settings
from .cache_manager import CacheManager
from .layer_executor import LayerExecutor
from .layer_loader import LayerLoader
from .memory_manager import MemoryManager
from .model_loader import ModelLoader
from .profiler import Profiler
from .scheduler import Scheduler
from .tokenizer_service import TokenizerService


@dataclass
class RuntimeState:
    model_name: str = settings.model_name
    provider: str = "none"
    layer_count: int = 0
    loaded_layers: list[int] = field(default_factory=list)
    tokens_per_second: float = 0.0
    last_prompt: str = ""
    last_response: str = ""
    last_duration: float = 0.0


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

    def load_model(self, model_name: str | None = None) -> dict:
        model_name = model_name or settings.model_name
        loaded = self.model_loader.load_model(model_name)
        self.tokenizer.load(model_name)
        self.state.model_name = model_name
        self.state.provider = loaded.provider
        self.state.layer_count = loaded.layer_count
        self.layer_loader = LayerLoader(max_active_layers=settings.max_active_layers)
        return self.model_info()

    def model_info(self) -> dict:
        return {
            "model_name": self.state.model_name,
            "loaded": self.model_loader.current is not None,
            "layer_count": self.state.layer_count,
            "provider": self.state.provider,
            "metadata": self.model_loader.get_metadata(),
        }

    def hardware_info(self) -> dict:
        snapshot = self.profiler.snapshot()
        return snapshot.__dict__

    def runtime_stats(self) -> dict:
        hardware = self.profiler.snapshot()
        ram_usage_percent = (
            100.0 - hardware.ram_free_gb / hardware.ram_total_gb * 100.0
            if hardware.ram_total_gb
            else 0.0
        )
        cpu_usage_percent = 0.0
        try:
            import psutil  # type: ignore

            cpu_usage_percent = float(psutil.cpu_percent(interval=None))
        except Exception:
            cpu_usage_percent = 0.0
        return {
            "loaded_layers": self.layer_loader.list_loaded_layers(),
            "ram_usage_percent": round(ram_usage_percent, 2),
            "cpu_usage_percent": round(cpu_usage_percent, 2),
            "tokens_per_second": round(self.state.tokens_per_second, 2),
            "active_model": self.state.model_name,
            "active_layers_count": len(self.layer_loader.list_loaded_layers()),
        }

    def generate(self, prompt: str, max_new_tokens: int = 64) -> dict:
        if self.model_loader.current is None:
            self.load_model(self.state.model_name)

        start = time.perf_counter()
        token_ids = self.tokenizer.encode(prompt)
        planned_layers = self.scheduler.plan(prompt, self.state.layer_count or 32)
        active_layers = []
        for layer_id in planned_layers[: settings.max_active_layers]:
            self.layer_loader.load_layer(layer_id)
            active_layers.append(layer_id)
            self.memory_manager.track_layer(layer_id)
            self.cache_manager.set(f"layer:{layer_id}", {"loaded": True})

        execution = self.layer_executor.execute(token_ids, active_layers)
        token_count = min(max_new_tokens, len(execution.logits) or 1)
        response_tokens = [f"layer{layer_id}" for layer_id in active_layers[:token_count]]
        response = " ".join(
            response_tokens
            or [
                "UAR",
                "runtime",
                "ready",
            ]
        )
        duration = max(time.perf_counter() - start, 1e-6)
        hardware = self.profiler.snapshot()
        ram_usage_percent = (
            100.0 - hardware.ram_free_gb / hardware.ram_total_gb * 100.0
            if hardware.ram_total_gb
            else 0.0
        )
        for layer_id in self.memory_manager.evict_if_needed(ram_usage_percent):
            self.layer_loader.unload_layer(layer_id)
        self.state.loaded_layers = self.layer_loader.list_loaded_layers()
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
