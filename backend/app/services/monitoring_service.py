from __future__ import annotations

from ..runtime.runtime_controller import RuntimeController


class MonitoringService:
    def __init__(self, runtime: RuntimeController) -> None:
        self.runtime = runtime

    def runtime_stats(self) -> dict:
        return self.runtime.runtime_stats()

