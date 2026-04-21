import redis.asyncio as redis
import json
from typing import Optional
from app.config import settings

class IdempotencyService:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.ttl_seconds = 86400
    
    async def check(self, idempotency_key: str) -> Optional[str]:
        result = await self.redis.get(f"idempotency:{idempotency_key}")
        if result:
            return result
        return None
    
    async def store(self, idempotency_key: str, message_id: str):
        await self.redis.setex(
            f"idempotency:{idempotency_key}",
            self.ttl_seconds,
            message_id
        )
    
    async def delete(self, idempotency_key: str):
        await self.redis.delete(f"idempotency:{idempotency_key}")