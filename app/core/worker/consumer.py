import asyncio
import uuid
from datetime import datetime
from typing import Optional
from app.core.circuit_breaker.breaker import get_circuit_breaker
from app.services.metrics import metrics
from app.models.notification import NotificationStatus
import logging

logger = logging.getLogger(__name__)

class NotificationWorker:
    def __init__(self, queue, notifier_service, db_session_factory):
        self.queue = queue
        self.notifier_service = notifier_service
        self.db_session_factory = db_session_factory
        self.running = False
        self.retry_delays = [1, 2, 4, 8, 16]
        self.max_concurrent = 10
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def start(self):
        self.running = True
        await self._consume()
    
    async def _consume(self):
        while self.running:
            try:
                message = await self.queue.pop(timeout=5)
                if not message:
                    await asyncio.sleep(0.1)
                    continue
                
                async with self.semaphore:
                    asyncio.create_task(self._process_with_retry(message))
                
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                await asyncio.sleep(1)
    
    async def _process_with_retry(self, message):
        notification_id = message["message_id"]
        provider_name = message["type"]
        retry_count = message.get("retry_count", 0)
        max_retries = message.get("max_retries", 3)
        
        await self._update_status(notification_id, NotificationStatus.PROCESSING)
        
        try:
            cb = get_circuit_breaker(provider_name)
            
            result = await cb.call(
                self.notifier_service.send_notification,
                provider_name,
                message["recipient"],
                message["payload"]
            )
            
            await self._update_status(notification_id, NotificationStatus.SUCCESS)
            await self.queue.ack(notification_id)
            metrics.record_success(provider_name)
            logger.info(f"Notification {notification_id} sent successfully")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Notification {notification_id} failed: {error_msg}")
            
            if retry_count < max_retries:
                await self._schedule_retry(message, retry_count + 1, error_msg)
            else:
                await self._move_to_dlq(notification_id, message, error_msg)
    
    async def _schedule_retry(self, message, new_retry_count, error_msg):
        notification_id = message["message_id"]
        
        await self._update_status(notification_id, NotificationStatus.RETRYING, error_msg)
        
        delay = self.retry_delays[min(new_retry_count - 1, len(self.retry_delays) - 1)]
        
        async def retry_later():
            await asyncio.sleep(delay)
            message["retry_count"] = new_retry_count
            await self.queue.push(message, priority="high")
        
        asyncio.create_task(retry_later())
        await self.queue.ack(notification_id)
        metrics.record_retry(message["type"])
        logger.info(f"Notification {notification_id} scheduled for retry {new_retry_count} in {delay}s")
    
    async def _move_to_dlq(self, notification_id, message, error_msg):
        await self._update_status(notification_id, NotificationStatus.DEAD, error_msg)
        
        from app.services.dlq_service import DLQService
        dlq_service = DLQService()
        await dlq_service.add_to_dlq(
            notification_id=notification_id,
            type=message["type"],
            recipient=message["recipient"],
            payload=message["payload"],
            failure_reason=error_msg,
            retry_count=message.get("retry_count", 0)
        )
        
        await self.queue.ack(notification_id)
        metrics.record_failure(message["type"])
        logger.error(f"Notification {notification_id} moved to DLQ after max retries")
    
    async def _update_status(self, notification_id: str, status: NotificationStatus, error_msg: str = None):
        from app.database import AsyncSessionLocal
        from app.models.notification import Notification
        
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            stmt = select(Notification).where(Notification.id == notification_id)
            result = await session.execute(stmt)
            notification = result.scalar_one_or_none()
            
            if notification:
                notification.status = status
                notification.updated_at = datetime.utcnow()
                if error_msg:
                    notification.last_error = error_msg
                if status == NotificationStatus.RETRYING:
                    notification.retry_count += 1
                await session.commit()