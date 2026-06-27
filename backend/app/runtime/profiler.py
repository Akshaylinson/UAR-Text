from __future__ import annotations

import os
import platform
from dataclasses import dataclass


@dataclass
class HardwareSnapshot:
    cpu: str
    cores: int
    ram_total_gb: float
    ram_free_gb: float
    gpu_available: bool
    disk_total_gb: float
    disk_free_gb: float


class Profiler:
    def snapshot(self) -> HardwareSnapshot:
        cpu = platform.processor() or platform.machine() or "unknown"
        cores = os.cpu_count() or 0
        ram_total_gb = 0.0
        ram_free_gb = 0.0
        disk_total_gb = 0.0
        disk_free_gb = 0.0
        gpu_available = False

        try:
            import psutil  # type: ignore

            vm = psutil.virtual_memory()
            du = psutil.disk_usage("/")
            ram_total_gb = round(vm.total / (1024**3), 2)
            ram_free_gb = round(vm.available / (1024**3), 2)
            disk_total_gb = round(du.total / (1024**3), 2)
            disk_free_gb = round(du.free / (1024**3), 2)
        except Exception:
            pass

        try:
            import torch  # type: ignore

            gpu_available = bool(torch.cuda.is_available())
        except Exception:
            gpu_available = False

        return HardwareSnapshot(
            cpu=cpu,
            cores=cores,
            ram_total_gb=ram_total_gb,
            ram_free_gb=ram_free_gb,
            gpu_available=gpu_available,
            disk_total_gb=disk_total_gb,
            disk_free_gb=disk_free_gb,
        )

