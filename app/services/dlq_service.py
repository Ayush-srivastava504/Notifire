from app.database import AsyncSessionLocal
from app.models.notification import DeadLetter
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select, delete
import uuid

class DLQService:
    async def add_to_dlq(self, notification_id: str, type: str, recipient: str, payload: Dict, failure_reason: str, retry_count: int):
        async with AsyncSessionLocal() as session:
            dlq_entry = DeadLetter(
                id=str(uuid.uuid4()),
                notification_id=notification_id,
                type=type,
                recipient=recipient,
                payload=payload,
                failure_reason=failure_reason,
                retry_count=retry_count,
                failed_at=datetime.utcnow()
            )
            session.add(dlq_entry)
            await session.commit()
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        async with AsyncSessionLocal() as session:
            stmt = select(DeadLetter).order_by(DeadLetter.failed_at.desc()).limit(limit).offset(offset)
            result = await session.execute(stmt)
            items = result.scalars().all()
            
            return [
                {
                    "id": item.id,
                    "notification_id": item.notification_id,
                    "type": item.type,
                    "recipient": item.recipient,
                    "payload": item.payload,
                    "failure_reason": item.failure_reason,
                    "retry_count": item.retry_count,
                    "failed_at": item.failed_at.isoformat()
                }
                for item in items
            ]
    
    async def replay(self, dlq_id: str, queue):
        async with AsyncSessionLocal() as session:
            stmt = select(DeadLetter).where(DeadLetter.id == dlq_id)
            result = await session.execute(stmt)
            item = result.scalar_one_or_none()
            
            if not item:
                return False
            
            message = {
                "message_id": str(uuid.uuid4()),
                "type": item.type,
                "recipient": item.recipient,
                "payload": item.payload,
                "retry_count": 0,
                "max_retries": 3
            }
            
            await queue.push(message, priority="high")
            
            await session.delete(item)
            await session.commit()
            
            return True
    
    async def replay_all(self, queue):
        async with AsyncSessionLocal() as session:
            stmt = select(DeadLetter)
            result = await session.execute(stmt)
            items = result.scalars().all()
            
            for item in items:
                message = {
                    "message_id": str(uuid.uuid4()),
                    "type": item.type,
                    "recipient": item.recipient,
                    "payload": item.payload,
                    "retry_count": 0,
                    "max_retries": 3
                }
                await queue.push(message, priority="high")
                await session.delete(item)
            
            await session.commit()
            return len(items)
    
    async def delete(self, dlq_id: str):
        async with AsyncSessionLocal() as session:
            stmt = delete(DeadLetter).where(DeadLetter.id == dlq_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0