import os
import re
import logging
import asyncio
from typing import Any, Callable

from config.config import settings
from memory.memory_manager import MemoryManager
from agents.provider import LLMProvider
from planner.planner import PlannerAgent
from workers.worker import WorkerAgent
from reviewer.reviewer import ReviewerAgent

logger = logging.getLogger("aythron.manager")

class ManagerAgent:
    """Manager Agent that coordinates all other agents and executes the goal orchestration loop."""
    
    def __init__(self, provider: LLMProvider, log_callback: Callable[[str], None] | None = None):
        self.provider = provider
        self.memory = MemoryManager(settings.workspace_dir)
        self.log_callback = log_callback
        
        # Initialize sub-agents
        self.planner = PlannerAgent(self.provider, settings.planner_model)
        self.reviewer = ReviewerAgent(self.provider, settings.reviewer_model)
        self.worker = WorkerAgent("Genesis Worker", self.provider, settings.worker_model)
        
        # Local execution state
        self.logs: list[str] = []
        self.is_running = False
        
    def log(self, message: str) -> None:
        """Logs a message locally, to Python logging, and triggers the callback if provided."""
        formatted = f"[{logging.getLevelName(logging.INFO)}] {message}"
        self.logs.append(formatted)
        logger.info(message)
        if self.log_callback:
            try:
                self.log_callback(formatted)
            except Exception as e:
                logger.error(f"Failed to execute log callback: {e}")
                
    def extract_and_write_files(self, worker_output: str) -> list[str]:
        """Extracts file blocks from worker output and writes them to the workspace."""
        written_files = []
        # Matches [FILE: filename] followed by code blocks
        pattern = r"\[FILE:\s*([^\]\s]+)\]\s*\n*```[a-zA-Z]*\n(.*?)\n```"
        matches = re.findall(pattern, worker_output, re.DOTALL)
        
        for filepath, content in matches:
            filepath = filepath.strip()
            # Prevent directory traversal attacks
            if ".." in filepath or filepath.startswith("/"):
                self.log(f"Warning: Blocked potential directory traversal file write to '{filepath}'")
                continue
                
            full_path = os.path.join(self.memory.workspace_dir, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            try:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.log(f"Wrote file successfully: {filepath}")
                written_files.append(filepath)
            except Exception as e:
                self.log(f"Error writing file {filepath}: {e}")
                
        return written_files

    async def execute_goal(self, goal: str) -> bool:
        """Orchestrates the entire multi-agent loop to accomplish the given goal."""
        if self.is_running:
            self.log("Orchestration is already running.")
            return False
            
        self.is_running = True
        self.logs.clear()
        
        self.log(f"Starting orchestration for goal: '{goal}'")
        
        try:
            # 1. Read context memory
            context_data = self.memory.read_file("context.md")
            project_state = self.memory.load_project_state()
            
            # 2. Planning phase
            self.log("Planning Phase: Activating Planner Agent...")
            plan = await self.planner.create_plan(goal, context_data)
            
            tasks = plan.get("tasks", [])
            if not tasks:
                self.log("Planner did not generate any tasks. Aborting.")
                self.is_running = False
                return False
                
            # Seed task metadata in tasks.json
            for task in tasks:
                task["status"] = "pending"
                task["attempts"] = 0
                task["output"] = ""
                task["feedback"] = ""
                
            self.memory.save_tasks({"tasks": tasks})
            self.log(f"Planner generated {len(tasks)} tasks.")
            
            # 3. Execution loop
            max_attempts_per_task = 3
            history_context = ""
            
            while True:
                # Reload tasks to ensure we have current state
                task_data = self.memory.load_tasks()
                tasks_list = task_data.get("tasks", [])
                
                # Check completions
                completed_ids = {t["id"] for t in tasks_list if t["status"] == "completed"}
                pending_tasks = [t for t in tasks_list if t["status"] == "pending"]
                in_progress_tasks = [t for t in tasks_list if t["status"] == "in_progress"]
                failed_tasks = [t for t in tasks_list if t["status"] == "failed"]
                
                if failed_tasks:
                    self.log(f"Execution failed: Task {failed_tasks[0]['id']} failed permanently.")
                    break
                    
                if not pending_tasks and not in_progress_tasks:
                    self.log("All tasks completed successfully!")
                    break
                    
                # Find eligible tasks (all dependencies must be completed)
                eligible_tasks = []
                for task in pending_tasks:
                    deps = task.get("dependencies", [])
                    if all(dep in completed_ids for dep in deps):
                        eligible_tasks.append(task)
                        
                if not eligible_tasks:
                    if pending_tasks:
                        self.log("Deadlock detected! Pending tasks have unresolved dependencies.")
                        break
                    await asyncio.sleep(0.5)
                    continue
                
                # Execute first eligible task
                task_to_run = eligible_tasks[0]
                task_id = task_to_run["id"]
                self.log(f"Executing task {task_id}: {task_to_run['description']}")
                
                # Set status to in_progress
                task_to_run["status"] = "in_progress"
                self.memory.save_tasks({"tasks": tasks_list})
                
                # Run worker
                task_to_run["attempts"] += 1
                worker_prompt = task_to_run["description"]
                if task_to_run["feedback"]:
                    worker_prompt += f"\n\nReviewer Feedback to fix:\n{task_to_run['feedback']}"
                    
                self.log(f"Activating Worker Agent (Attempt {task_to_run['attempts']}/{max_attempts_per_task})...")
                worker_output = await self.worker.execute_task(
                    task_description=worker_prompt,
                    context=context_data,
                    history_context=history_context
                )
                
                # Attempt to extract files from worker output
                written = self.extract_and_write_files(worker_output)
                
                # Run reviewer
                self.log("Activating Reviewer Agent...")
                review = await self.reviewer.review_work(
                    task_description=task_to_run["description"],
                    worker_output=worker_output,
                    context=context_data
                )
                
                if review.get("approved", False):
                    self.log(f"Task {task_id} APPROVED by Reviewer: {review.get('feedback')}")
                    task_to_run["status"] = "completed"
                    task_to_run["output"] = worker_output
                    task_to_run["feedback"] = ""
                    
                    # Add to history context for downstream tasks
                    history_context += f"\nTask {task_id}: {task_to_run['description']}\nOutput:\n{worker_output}\n---\n"
                else:
                    self.log(f"Task {task_id} REJECTED by Reviewer: {review.get('feedback')}")
                    task_to_run["feedback"] = review.get("feedback", "Rejected with no feedback.")
                    
                    if task_to_run["attempts"] >= max_attempts_per_task:
                        self.log(f"Task {task_id} exceeded maximum retry attempts. Marking as failed.")
                        task_to_run["status"] = "failed"
                    else:
                        task_to_run["status"] = "pending" # Reset to pending to retry
                        
                # Update memory
                self.memory.save_tasks({"tasks": tasks_list})
                await asyncio.sleep(0.5)
                
            # 4. Wrap up and update memory state
            final_tasks = self.memory.load_tasks().get("tasks", [])
            success = all(t["status"] == "completed" for t in final_tasks)
            
            # Update project state in memory
            state = self.memory.load_project_state()
            if success:
                state["completed_features"].append(f"Accomplished goal: {goal}")
            self.memory.save_project_state(state)
            
            # Session log update
            outcome = "Orchestrated goal successfully." if success else "Goal execution failed."
            self.memory.append_session_log(
                activity=f"Goal Execution: {goal}",
                outcome=outcome,
                next_steps=["Verify results in workspace"]
            )
            
            self.is_running = False
            return success
            
        except Exception as e:
            self.log(f"Execution crashed due to unhandled error: {e}")
            self.is_running = False
            raise
