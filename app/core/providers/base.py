from abc import ABC, abstractmethod
from typing import Dict, Any
import httpx
import asyncio

class BaseProvider(ABC):
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
    
    @abstractmethod
    async def send(self, recipient: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

class EmailProvider(BaseProvider):
    async def send(self, recipient: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                "https://api.email.com/send",
                json={"to": recipient, "subject": payload.get("subject"), "body": payload.get("body")},
                headers={"Authorization": "Bearer test-key"}
            )
            response.raise_for_status()
            return {"status": "sent", "provider": "email"}

class SlackProvider(BaseProvider):
    async def send(self, recipient: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                json={"channel": recipient, "text": payload.get("message")},
                headers={"Authorization": "Bearer test-token"}
            )
            response.raise_for_status()
            return {"status": "sent", "provider": "slack"}

class WebhookProvider(BaseProvider):
    async def send(self, recipient: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(recipient, json=payload)
            response.raise_for_status()
            return {"status": "delivered", "provider": "webhook", "status_code": response.status_code}

class ProviderFactory:
    @staticmethod
    def get_provider(provider_type: str):
        from app.config import settings
        config = settings.PROVIDER_CONFIGS.get(provider_type, {})
        timeout = config.get("timeout", 5)
        
        if provider_type == "email":
            return EmailProvider(timeout=timeout)
        elif provider_type == "slack":
            return SlackProvider(timeout=timeout)
        elif provider_type == "webhook":
            return WebhookProvider(timeout=timeout)
        else:
            raise ValueError(f"Unknown provider: {provider_type}")