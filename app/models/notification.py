from sqlalchemy import Column, String, DateTime, Integer, JSON, Enum, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime
import enum
import uuid

Base = declarative_base()

class NotificationStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD = "dead"

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String(50), nullable=False)
    recipient = Column(String(500), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.QUEUED)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    idempotency_key = Column(String(255), unique=True, index=True, nullable=True)

class DeadLetter(Base):
    __tablename__ = "dead_letters"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    notification_id = Column(String(36), nullable=False)
    type = Column(String(50))
    recipient = Column(String(500))
    payload = Column(JSON)
    failure_reason = Column(Text, nullable=False)
    retry_count = Column(Integer, default=0)
    failed_at = Column(DateTime, default=datetime.utcnow)