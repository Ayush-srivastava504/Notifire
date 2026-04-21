from pydantic_settings import BaseSettings
from typing import Dict
import os

class Settings(BaseSettings):
    APP_NAME: str = "Notifire"
    DEBUG: bool = False
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/notifire")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    QUEUE_MAX_SIZE: int = 10000
    DEFAULT_RETRY_ATTEMPTS: int = 3
    DEFAULT_RETRY_DELAY: int = 1
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_TIMEOUT: int = 30
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    API_KEY: str = os.getenv("API_KEY", "test-key-123")
    PROVIDER_CONFIGS: Dict = {
        "email": {"timeout": 5, "rate_limit": 10, "endpoint": "https://api.email.com/send"},
        "slack": {"timeout": 3, "rate_limit": 20, "endpoint": "https://slack.com/api/chat.postMessage"},
        "webhook": {"timeout": 10, "rate_limit": 50, "endpoint": None}
    }

settings = Settings()