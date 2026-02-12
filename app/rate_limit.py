from __future__ import annotations

import time
from dataclasses import dataclass

from app.config import settings


def parse_rate_limit(s: str) -> tuple[int, int]:
    # "<requests>/<seconds>" e.g. "50/60"
    parts = s.strip().split("/")
    if len(parts) != 2:
        return 50, 60
    return int(parts[0]), int(parts[1])


@dataclass
class FixedWindowLimiter:
    limit: int
    window_seconds: int
    count: int = 0
    window_start: float = 0.0

    def allow(self) -> bool:
        now = time.time()
        if self.window_start == 0.0 or now - self.window_start >= self.window_seconds:
            self.window_start = now
            self.count = 0
        self.count += 1
        return self.count <= self.limit


_global_limiter = FixedWindowLimiter(*parse_rate_limit(settings.RATE_LIMIT))
