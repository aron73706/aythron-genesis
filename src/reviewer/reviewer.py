import json
import logging
import re
from typing import Any
from agents.base import BaseAgent
from agents.provider import LLMProvider

logger = logging.getLogger("aythron.reviewer")

REVIEWER_SYSTEM_PROMPT = """You are the Quality Reviewer Agent for Aythron Genesis.
Your job is to critically review the deliverables produced by Worker Agents.
You must analyze the task description, the project context, and the worker's output, then output a valid JSON object.

Your output must follow this JSON schema EXACTLY:
{
  "approved": true,
  "feedback": "Detailed explanation of findings or congratulations on a job well done"
}

If the work has deficiencies, bugs, missing requirements, or formatting errors, set "approved" to false and provide actionable feedback.
If the work is complete, accurate, and ready for integration, set "approved" to true.

Do NOT output any conversational text or explanations outside the JSON block. Output ONLY the raw JSON block.
"""

class ReviewerAgent(BaseAgent):
    """Reviewer Agent checks deliverables against requirements and approves/rejects them."""
    
    def __init__(self, provider: LLMProvider, model: str):
        super().__init__(
            name="Genesis Reviewer",
            role="Reviewer",
            provider=provider,
            model=model,
            system_prompt=REVIEWER_SYSTEM_PROMPT
        )
        
    async def review_work(self, task_description: str, worker_output: str, context: str) -> dict[str, Any]:
        """Reviews the work and returns approved status and feedback."""
        prompt = (
            f"Task Description:\n{task_description}\n\n"
            f"Worker Output:\n{worker_output}\n\n"
            f"Project Context:\n{context}\n\n"
            f"Analyze and output the review JSON."
        )
        raw_response = await self.execute(prompt)
        
        # Clean up any potential markdown code block wrappers
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)
            cleaned = cleaned.strip()
            
        try:
            review = json.loads(cleaned)
            if "approved" not in review or "feedback" not in review:
                raise ValueError("Reviewer output JSON is missing required fields 'approved' or 'feedback'")
            return review
        except Exception as e:
            logger.error(f"Failed to parse Reviewer JSON output. Raw output was:\n{raw_response}")
            raise RuntimeError(f"Reviewer response was not valid JSON: {e}")
