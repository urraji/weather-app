import time
from collections import deque
from dataclasses import dataclass
from app.config import settings
from app.metrics import openweather_circuit_open_total

@dataclass
class CircuitState:
    opened_until: float = 0.0
    failures: deque = None
    def __post_init__(self):
        if self.failures is None:
            self.failures = deque()

class CircuitBreaker:
    def __init__(self):
        self.state = CircuitState()
    def allow(self) -> bool:
        return time.time() >= self.state.opened_until
    def record_failure(self):
        now = time.time()
        self.state.failures.append(now)
        window = settings.CIRCUIT_BREAKER_WINDOW_SECONDS
        while self.state.failures and (now - self.state.failures[0]) > window:
            self.state.failures.popleft()
        if len(self.state.failures) >= settings.CIRCUIT_BREAKER_FAILS:
            self.state.opened_until = now + settings.CIRCUIT_BREAKER_OPEN_SECONDS
            openweather_circuit_open_total.inc()
            self.state.failures.clear()
    def record_success(self):
        self.state.failures.clear()

breaker = CircuitBreaker()
