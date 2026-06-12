import logging
from agents.base import BaseAgent
from agents.provider import LLMProvider

logger = logging.getLogger("aythron.worker")

WORKER_SYSTEM_PROMPT = """You are a specialized Worker Agent in the Aythron Genesis platform.
Your job is to execute the assigned task as thoroughly and professionally as possible.

If the task requires generating code or files, you must structure your response clearly:
1. Explain what you are doing (reasoning/analysis).
2. If creating or modifying a file, specify the filename and block format:
   [FILE: path/to/file.ext]
   ```
   code/content here
   ```
   Ensure you provide the FULL file content rather than snippets, unless instructed otherwise.

Guidelines:
- Produce production-quality code with type hints, comments, error handling, and modular structure.
- Follow architectural rules, naming conventions, and project context provided to you.
- Always output clean, complete, and correct work.
"""

class WorkerAgent(BaseAgent):
    """Worker Agent executes concrete tasks and produces files or text deliverables."""
    
    def __init__(self, name: str, provider: LLMProvider, model: str):
        super().__init__(
            name=name,
            role="Worker",
            provider=provider,
            model=model,
            system_prompt=WORKER_SYSTEM_PROMPT
        )
        
    async def execute_task(self, task_description: str, context: str, history_context: str = "") -> str:
        """Executes a single task based on description and context."""
        prompt = (
            f"Task to Execute:\n{task_description}\n\n"
            f"Project Context:\n{context}\n\n"
        )
        if history_context:
            prompt += f"Previous Tasks & Outcomes:\n{history_context}\n\n"
            
        prompt += "Please execute the task and provide your output."
        return await self.execute(prompt)
