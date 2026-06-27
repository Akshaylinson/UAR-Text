from __future__ import annotations

from ..runtime.profiler import Profiler


class HardwareService:
    def __init__(self) -> None:
        self.profiler = Profiler()

    def get_hardware_info(self) -> dict:
        return self.profiler.snapshot().__dict__

