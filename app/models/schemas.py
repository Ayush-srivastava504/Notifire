from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    email = "email"
    slack = "slack"
    webhook = "webhook"

class NotificationRequest(BaseModel):
    type: NotificationType
    recipient: str
    payload: Dict[str, Any]
    retry_policy: Optional[str] = "default"
    max_retries: Optional[int] = 3
    idempotency_key: Optional[str] = None

    @validator('recipient')
    def validate_recipient(cls, v, values):
        if values.get('type') == 'email' and '@' not in v:
            raise ValueError('Invalid email address')
        return v

class NotificationResponse(BaseModel):
    message_id: str
    status: str
    queued_at: datetime

class DLQItemResponse(BaseModel):
    id: str
    notification_id: str
    type: str
    recipient: str
    failure_reason: str
    failed_at: datetime

class MetricsResponse(BaseModel):
    total_notifications: int
    success_rate: float
    queue_depth: int
    circuit_breaker_states: Dict[str, str]