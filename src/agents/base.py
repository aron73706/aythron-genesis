import logging
from typing import Any
from agents.provider import LLMProvider

logger = logging.getLogger("aythron.agent")

class BaseAgent:
    """Base class for all agents in Aythron Genesis."""
    
    def __init__(self, name: str, role: str, provider: LLMProvider, model: str, system_prompt: str):
        self.name = name
        self.role = role
        self.provider = provider
        self.model = model
        self.system_prompt = system_prompt
        self.history: list[dict[str, str]] = []
        
    def _get_messages(self, user_content: str) -> list[dict[str, str]]:
        """Compiles system and user prompts into chat messages."""
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content}
        ]
        
    async def execute(self, prompt: str, **kwargs: Any) -> str:
        """Executes the agent logic by calling the LLM provider."""
        logger.info(f"Agent '{self.name}' ({self.role}) executing task with model '{self.model}'")
        messages = self._get_messages(prompt)
        
        try:
            response = await self.provider.generate(messages, model=self.model, **kwargs)
            self.history.append({"prompt": prompt, "response": response})
            logger.info(f"Agent '{self.name}' completed execution successfully")
            return response
        except Exception as e:
            logger.error(f"Agent '{self.name}' failed to generate response: {e}")
            raise
