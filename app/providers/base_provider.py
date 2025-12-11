from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator

class BaseProvider(ABC):
    @abstractmethod
    def verify_token(self, token: str) -> bool:
        pass
    
    @abstractmethod
    async def chat_completion(self, request_data: Dict[str, Any], token: str) -> AsyncGenerator[str, None]:
        pass