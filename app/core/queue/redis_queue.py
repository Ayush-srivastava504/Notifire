import redis.asyncio as redis
import json
import time
from typing import Optional, Dict, Any
from .base import BaseQueue

class RedisQueue(BaseQueue):
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.queue_key = "notifire:queue"
        self.processing_key = "notifire:processing"
    
    async def push(self, message: Dict[str, Any], priority: str = "normal"):
        priority_map = {"high": 1, "normal": 2, "low": 3}
        score = priority_map.get(priority, 2)
        message_json = json.dumps(message)
        await self.redis.zadd(self.queue_key, {message_json: score})
    
    async def pop(self, timeout: int = 5) -> Optional[Dict[str, Any]]:
        result = await self.redis.bzpopmin(self.queue_key, timeout=timeout)
        if result:
            _, message_json, _ = result
            message = json.loads(message_json)
            await self.redis.hset(
                self.processing_key,
                message["message_id"],
                json.dumps({"message": message, "timestamp": time.time()})
            )
            return message
        return None
    
    async def ack(self, message_id: str):
        await self.redis.hdel(self.processing_key, message_id)
    
    async def nack(self, message_id: str):
        data = await self.redis.hget(self.processing_key, message_id)
        if data:
            message_data = json.loads(data)
            message = message_data["message"]
            await self.push(message)
            await self.ack(message_id)
    
    async def size(self) -> int:
        return await self.redis.zcard(self.queue_key)
    
    async def requeue_all(self):
        processing_items = await self.redis.hgetall(self.processing_key)
        for item in processing_items.values():
            data = json.loads(item)
            message = data["message"]
            await self.push(message)
            await self.ack(message["message_id"])