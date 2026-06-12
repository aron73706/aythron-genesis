import json
import logging
import re
from typing import Any
from agents.base import BaseAgent
from agents.provider import LLMProvider

logger = logging.getLogger("aythron.planner")

PLANNER_SYSTEM_PROMPT = """You are the Lead Planner Agent for Aythron Genesis.
Your job is to break down a high-level goal into a sequence of actionable, modular tasks.
You must analyze the goal and any provided context, then output a valid, parsable JSON object.

Your output must follow this JSON schema EXACTLY:
{
  "tasks": [
    {
      "id": "T1",
      "description": "Short, concrete description of the task",
      "dependencies": [],
      "assignee": "Worker"
    },
    {
      "id": "T2",
      "description": "Next task building on T1",
      "dependencies": ["T1"],
      "assignee": "Worker"
    }
  ]
}

Guidelines:
1. Identify all deliverables and split them into separate tasks.
2. Determine dependencies correctly (e.g., cannot test a file before creating it).
3. Assign each task to "Worker" (which represents Worker Agents).
4. Do NOT output any conversational text or explanation. Output ONLY the raw JSON block.
"""

class PlannerAgent(BaseAgent):
    """Planner Agent decomposes goals into dependency-tracked tasks."""
    
    def __init__(self, provider: LLMProvider, model: str):
        super().__init__(
            name="Genesis Planner",
            role="Planner",
            provider=provider,
            model=model,
            system_prompt=PLANNER_SYSTEM_PROMPT
        )
        
    async def create_plan(self, goal: str, context: str) -> dict[str, Any]:
        """Generates a task list JSON from the goal and context."""
        prompt = f"Goal:\n{goal}\n\nContext:\n{context}\n\nGenerate the task list in JSON format."
        raw_response = await self.execute(prompt)
        
        # Clean up any potential markdown code block wrappers
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            # Strip off ```json and ```
            cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)
            cleaned = cleaned.strip()
            
        try:
            plan = json.loads(cleaned)
            if "tasks" not in plan:
                raise ValueError("Planner output JSON is missing key 'tasks'")
            return plan
        except Exception as e:
            logger.error(f"Failed to parse Planner JSON output. Raw output was:\n{raw_response}")
            raise RuntimeError(f"Planner response was not valid JSON: {e}")
