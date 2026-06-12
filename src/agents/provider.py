from abc import ABC, abstractmethod
import logging
import httpx
from typing import Any

logger = logging.getLogger("aythron.provider")

class LLMProvider(ABC):
    """Abstract base class for LLM Providers."""
    
    @abstractmethod
    async def generate(self, messages: list[dict[str, str]], model: str | None = None, **kwargs) -> str:
        """Generate a response for a given list of chat messages."""
        pass

class OllamaProvider(LLMProvider):
    """Provider for interacting with local Ollama instances."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=120.0)
        
    async def generate(self, messages: list[dict[str, str]], model: str | None = None, **kwargs) -> str:
        if not model:
            raise ValueError("A model name must be provided for Ollama.")
            
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": kwargs.get("options", {})
        }
        
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
        except httpx.ConnectError:
            error_msg = f"Failed to connect to Ollama at {url}. Is Ollama running?"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                error_msg = f"Model '{model}' not found in Ollama. Please run `ollama pull {model}`."
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            error_msg = f"Ollama HTTP error: {e.response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            logger.exception("Unexpected error in Ollama generation")
            raise RuntimeError(f"Ollama generation failed: {e}")

class MockProvider(LLMProvider):
    """Mock Provider for unit testing or fallback mode."""
    
    def __init__(self, response_map: dict[str, str] | None = None, default_response: str = "Mock response"):
        self.response_map = response_map or {}
        self.default_response = default_response
        self.history = []
        
    async def generate(self, messages: list[dict[str, str]], model: str | None = None, **kwargs) -> str:
        self.history.append((messages, model, kwargs))
        # Find matching prompt in response map
        last_message = messages[-1]["content"] if messages else ""
        
        # Match the longest/most specific keys first to avoid substring collision
        sorted_keys = sorted(self.response_map.keys(), key=len, reverse=True)
        for key in sorted_keys:
            if key in last_message:
                return self.response_map[key]
                
        return self.default_response
