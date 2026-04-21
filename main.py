import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routes import notifications, dlq, admin
from app.core.queue.redis_queue import RedisQueue
from app.core.worker.consumer import NotificationWorker
from app.core.circuit_breaker.breaker import circuit_breakers
from app.services.metrics import metrics
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

queue = None
worker = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global queue, worker
    logger.info("Starting Notification Engine...")
    queue = RedisQueue(settings.REDIS_URL)
    from app.services.dlq_service import DLQService
    from app.services.notifier import NotifierService
    from app.database import get_db
    dlq_service = DLQService()
    notifier_service = NotifierService(queue, dlq_service)
    worker = NotificationWorker(queue, notifier_service, get_db)
    import asyncio
    asyncio.create_task(worker.start())
    yield
    logger.info("Shutting down...")
    if worker:
        worker.running = False

app = FastAPI(title="Notifire", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notifications.router, prefix="/v1", tags=["notifications"])
app.include_router(dlq.router, prefix="/v1", tags=["dead-letter-queue"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])

@app.get("/health")
async def health():
    return {"status": "healthy", "queue_size": await queue.size() if queue else 0}

@app.get("/metrics")
async def get_metrics():
    return metrics.get_all()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)