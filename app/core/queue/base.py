from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseQueue(ABC):
    @abstractmethod
    async def push(self, message: Dict[str, Any], priority: str = "normal"):
        pass
    
    @abstractmethod
    async def pop(self, timeout: int = 5) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def ack(self, message_id: str):
        pass
    
    @abstractmethod
    async def nack(self, message_id: str):
        pass
    
    @abstractmethod
    async def size(self) -> int:
        pass