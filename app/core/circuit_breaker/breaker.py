import time
from enum import Enum
from typing import Dict, Optional, Callable, Awaitable, Any


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, timeout: int = 30):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change = time.time()

    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        if not self._allow_request():
            raise Exception(f"Circuit breaker '{self.name}' is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _allow_request(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self.last_failure_time and time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = time.time()
                return True
            return False

        return True

    def _on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self._reset()
        else:
            self.failure_count = 0

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()
            self.success_count = 0
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()

    def _reset(self):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = time.time()

    def get_state(self) -> str:
        return self.state.value


circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(provider: str) -> CircuitBreaker:
    if provider not in circuit_breakers:
        from app.config import settings

        circuit_breakers[provider] = CircuitBreaker(
            provider,
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            timeout=settings.CIRCUIT_BREAKER_TIMEOUT
        )

    return circuit_breakers[provider]