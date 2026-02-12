from __future__ import annotations

import time
from dataclasses import dataclass

from app.config import settings


@dataclass
class CircuitBreaker:
    failures: int = 0
    open_until: float = 0.0

    def is_open(self) -> bool:
        return time.time() < self.open_until

    def record_success(self) -> None:
        self.failures = 0
        self.open_until = 0.0

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= settings.CIRCUIT_BREAKER_FAILS:
            self.open_until = time.time() + settings.CIRCUIT_BREAKER_OPEN_SECONDS
