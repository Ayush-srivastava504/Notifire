from fastapi import APIRouter, Depends, HTTPException, Header
from app.core.queue.redis_queue import RedisQueue
from app.services.metrics import metrics
from app.core.circuit_breaker.breaker import circuit_breakers, get_circuit_breaker
from app.config import settings
from app.database import AsyncSessionLocal
from app.models.notification import Notification
from sqlalchemy import func, select

router = APIRouter()
queue = RedisQueue(settings.REDIS_URL)

async def verify_admin(api_key: str = Header(..., alias="X-Admin-Key")):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return api_key

@router.get("/metrics")
async def get_metrics(api_key: str = Depends(verify_admin)):
    return metrics.get_all()

@router.post("/circuit-breaker/{provider}/reset")
async def reset_circuit_breaker(provider: str, api_key: str = Depends(verify_admin)):
    cb = get_circuit_breaker(provider)
    cb._reset()
    return {"status": "reset", "provider": provider, "state": cb.get_state()}

@router.get("/circuit-breaker/{provider}")
async def get_circuit_breaker_status(provider: str, api_key: str = Depends(verify_admin)):
    cb = get_circuit_breaker(provider)
    return {
        "provider": provider,
        "state": cb.get_state(),
        "failure_count": cb.failure_count,
        "last_failure_time": cb.last_failure_time
    }

@router.post("/queue/flush")
async def flush_queue(api_key: str = Depends(verify_admin)):
    await queue.requeue_all()
    return {"status": "flushed", "message": "All processing messages requeued"}

@router.get("/queue/stats")
async def get_queue_stats(api_key: str = Depends(verify_admin)):
    async with AsyncSessionLocal() as session:
        total_query = select(func.count()).select_from(Notification)
        total_result = await session.execute(total_query)
        total = total_result.scalar()
        
        success_query = select(func.count()).where(Notification.status == "success")
        success_result = await session.execute(success_query)
        success = success_result.scalar()
        
        failed_query = select(func.count()).where(Notification.status == "failed")
        failed_result = await session.execute(failed_query)
        failed = failed_result.scalar()
        
        dead_query = select(func.count()).where(Notification.status == "dead")
        dead_result = await session.execute(dead_query)
        dead = dead_result.scalar()
        
        return {
            "queue_depth": await queue.size(),
            "total_notifications": total,
            "successful": success,
            "failed": failed,
            "dead": dead
        }