from typing import Dict, Any
from app.core.providers.base import ProviderFactory
from app.core.circuit_breaker.breaker import get_circuit_breaker
from app.services.metrics import metrics
import time

class NotifierService:
    def __init__(self, queue, dlq_service):
        self.queue = queue
        self.dlq_service = dlq_service
    
    async def send_notification(self, provider_type: str, recipient: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            provider = ProviderFactory.get_provider(provider_type)
            result = await provider.send(recipient, payload)
            
            elapsed = time.time() - start_time
            metrics.record_latency(provider_type, elapsed)
            
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            metrics.record_latency(provider_type, elapsed)
            raise e