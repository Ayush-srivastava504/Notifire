from typing import Dict, List
from collections import defaultdict
import time
from datetime import datetime, timedelta

class MetricsCollector:
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.retry_count = 0
        self.provider_success: Dict[str, int] = defaultdict(int)
        self.provider_failure: Dict[str, int] = defaultdict(int)
        self.provider_retry: Dict[str, int] = defaultdict(int)
        self.latencies: Dict[str, List[float]] = defaultdict(list)
        self.circuit_breaker_states: Dict[str, str] = {}
        self.start_time = time.time()
    
    def record_success(self, provider: str):
        self.total_requests += 1
        self.successful_requests += 1
        self.provider_success[provider] += 1
    
    def record_failure(self, provider: str):
        self.total_requests += 1
        self.failed_requests += 1
        self.provider_failure[provider] += 1
    
    def record_retry(self, provider: str):
        self.retry_count += 1
        self.provider_retry[provider] += 1
    
    def record_latency(self, provider: str, latency: float):
        self.latencies[provider].append(latency)
        if len(self.latencies[provider]) > 1000:
            self.latencies[provider] = self.latencies[provider][-1000:]
    
    def get_success_rate(self) -> float:
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100
    
    def get_average_latency(self, provider: str) -> float:
        latencies = self.latencies.get(provider, [])
        if not latencies:
            return 0.0
        return sum(latencies) / len(latencies)
    
    def get_uptime(self) -> float:
        return time.time() - self.start_time
    
    def get_all(self) -> Dict:
        from app.core.circuit_breaker.breaker import circuit_breakers
        
        for name, cb in circuit_breakers.items():
            self.circuit_breaker_states[name] = cb.get_state()
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.get_success_rate(),
            "retry_count": self.retry_count,
            "uptime_seconds": self.get_uptime(),
            "provider_stats": {
                provider: {
                    "success": self.provider_success[provider],
                    "failure": self.provider_failure[provider],
                    "retry": self.provider_retry[provider],
                    "avg_latency_ms": self.get_average_latency(provider) * 1000
                }
                for provider in set(list(self.provider_success.keys()) + list(self.provider_failure.keys()))
            },
            "circuit_breaker_states": self.circuit_breaker_states
        }

metrics = MetricsCollector()