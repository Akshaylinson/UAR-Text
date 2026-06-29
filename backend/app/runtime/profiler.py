from __future__ import annotations

import os
import platform
from dataclasses import dataclass


@dataclass
class HardwareSnapshot:
    cpu: str
    cpu_cores: int
    cpu_threads: int
    cpu_usage_percent: float
    ram_total_gb: float
    ram_used_gb: float
    ram_free_gb: float
    ram_usage_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_free_gb: float
    disk_usage_percent: float
    gpu_available: bool
    gpu_memory_gb: float


class Profiler:
    def snapshot(self) -> HardwareSnapshot:
        cpu = platform.processor() or platform.machine() or "unknown"
        cpu_threads = os.cpu_count() or 0
        cpu_cores = cpu_threads
        cpu_usage_percent = 0.0
        ram_total_gb = 0.0
        ram_used_gb = 0.0
        ram_free_gb = 0.0
        ram_usage_percent = 0.0
        disk_total_gb = 0.0
        disk_used_gb = 0.0
        disk_free_gb = 0.0
        disk_usage_percent = 0.0
        gpu_available = False
        gpu_memory_gb = 0.0

        try:
            import psutil  # type: ignore

            vm = psutil.virtual_memory()
            du = psutil.disk_usage("/")
            cpu_usage_percent = float(psutil.cpu_percent(interval=None))
            ram_total_gb = round(vm.total / (1024**3), 2)
            ram_used_gb = round(vm.used / (1024**3), 2)
            ram_free_gb = round(vm.available / (1024**3), 2)
            ram_usage_percent = round(vm.percent, 2)
            disk_total_gb = round(du.total / (1024**3), 2)
            disk_used_gb = round(du.used / (1024**3), 2)
            disk_free_gb = round(du.free / (1024**3), 2)
            disk_usage_percent = round(du.percent, 2)
        except Exception:
            pass

        try:
            import torch  # type: ignore

            gpu_available = bool(torch.cuda.is_available())
            if gpu_available:
                device_index = torch.cuda.current_device()
                props = torch.cuda.get_device_properties(device_index)
                gpu_memory_gb = round(props.total_memory / (1024**3), 2)
        except Exception:
            gpu_available = False
            gpu_memory_gb = 0.0

        return HardwareSnapshot(
            cpu=cpu,
            cpu_cores=cpu_cores,
            cpu_threads=cpu_threads,
            cpu_usage_percent=round(cpu_usage_percent, 2),
            ram_total_gb=ram_total_gb,
            ram_used_gb=ram_used_gb,
            ram_free_gb=ram_free_gb,
            ram_usage_percent=ram_usage_percent,
            disk_total_gb=disk_total_gb,
            disk_used_gb=disk_used_gb,
            disk_free_gb=disk_free_gb,
            disk_usage_percent=disk_usage_percent,
            gpu_available=gpu_available,
            gpu_memory_gb=gpu_memory_gb,
        )
