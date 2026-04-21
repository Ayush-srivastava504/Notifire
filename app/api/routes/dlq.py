from fastapi import APIRouter, HTTPException, Depends, Header
from app.services.dlq_service import DLQService
from app.models.schemas import DLQItemResponse
from app.core.queue.redis_queue import RedisQueue
from app.config import settings
from typing import List

router = APIRouter()
dlq_service = DLQService()
queue = RedisQueue(settings.REDIS_URL)

async def verify_admin_key(api_key: str = Header(..., alias="X-Admin-Key")):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return api_key

@router.get("/dlq", response_model=List[DLQItemResponse])
async def get_dead_letters(limit: int = 100, offset: int = 0, api_key: str = Depends(verify_admin_key)):
    items = await dlq_service.get_all(limit, offset)
    return items

@router.post("/dlq/{dlq_id}/replay")
async def replay_dlq_item(dlq_id: str, api_key: str = Depends(verify_admin_key)):
    success = await dlq_service.replay(dlq_id, queue)
    if not success:
        raise HTTPException(status_code=404, detail="DLQ item not found")
    return {"status": "replayed", "dlq_id": dlq_id}

@router.post("/dlq/replay-all")
async def replay_all_dlq(api_key: str = Depends(verify_admin_key)):
    count = await dlq_service.replay_all(queue)
    return {"status": "replayed", "count": count}

@router.delete("/dlq/{dlq_id}")
async def delete_dlq_item(dlq_id: str, api_key: str = Depends(verify_admin_key)):
    deleted = await dlq_service.delete(dlq_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="DLQ item not found")
    return {"status": "deleted", "dlq_id": dlq_id}