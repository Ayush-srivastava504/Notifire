from fastapi import APIRouter, HTTPException, Depends, Header
from app.models.schemas import NotificationRequest, NotificationResponse
from app.core.queue.redis_queue import RedisQueue
from app.services.idempotency import IdempotencyService
from app.config import settings
from datetime import datetime
import uuid
from app.database import AsyncSessionLocal
from app.models.notification import Notification, NotificationStatus
from sqlalchemy import select

router = APIRouter()
queue = RedisQueue(settings.REDIS_URL)
idempotency_service = IdempotencyService()

async def verify_api_key(api_key: str = Header(..., alias="X-API-Key")):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

@router.post("/notify", response_model=NotificationResponse)
async def send_notification(
    request: NotificationRequest,
    api_key: str = Depends(verify_api_key)
):
    if request.idempotency_key:
        existing = await idempotency_service.check(request.idempotency_key)
        if existing:
            return NotificationResponse(
                message_id=existing,
                status="already_processed",
                queued_at=datetime.utcnow()
            )

    message_id = str(uuid.uuid4())

    async with AsyncSessionLocal() as session:
        notification = Notification(
            id=message_id,
            type=request.type.value,
            recipient=request.recipient,
            payload=request.payload,
            status=NotificationStatus.QUEUED,
            max_retries=request.max_retries,
            idempotency_key=request.idempotency_key
        )
        session.add(notification)
        await session.commit()

    message = {
        "message_id": message_id,
        "type": request.type.value,
        "recipient": request.recipient,
        "payload": request.payload,
        "retry_count": 0,
        "max_retries": request.max_retries
    }

    await queue.push(message, priority="normal")

    if request.idempotency_key:
        await idempotency_service.store(request.idempotency_key, message_id)

    return NotificationResponse(
        message_id=message_id,
        status="queued",
        queued_at=datetime.utcnow()
    )

@router.get("/notify/{message_id}")
async def get_notification_status(
    message_id: str,
    api_key: str = Depends(verify_api_key)
):
    async with AsyncSessionLocal() as session:
        stmt = select(Notification).where(Notification.id == message_id)
        result = await session.execute(stmt)
        notification = result.scalar_one_or_none()

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        return {
            "message_id": notification.id,
            "status": notification.status.value,
            "retry_count": notification.retry_count,
            "last_error": notification.last_error,
            "created_at": notification.created_at.isoformat(),
            "updated_at": notification.updated_at.isoformat()
        }