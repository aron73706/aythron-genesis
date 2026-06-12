import os
import asyncio
import logging
from typing import Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config.config import settings
from agents.provider import OllamaProvider, MockProvider
from agents.manager import ManagerAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("aythron.api")

app = FastAPI(title="Aythron Genesis API", version="0.1.0")

# Enable CORS for local UI development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Runtime configuration state
class RuntimeConfig:
    def __init__(self):
        self.provider_type = "mock"  # default to mock so it runs immediately out-of-the-box
        self.ollama_host = settings.ollama_host
        self.default_model = settings.default_model
        
        # Initialize providers
        self.ollama_provider = OllamaProvider(self.ollama_host)
        
        # Build interactive response maps for Mock mode
        self.mock_provider = MockProvider(
            response_map={
                # Planner queries
                "Generate the task list in JSON format": """
{
  "tasks": [
    {
      "id": "T1",
      "description": "Create the fibonacci.py script containing the fibonacci function",
      "dependencies": [],
      "assignee": "Worker"
    },
    {
      "id": "T2",
      "description": "Create a test_fibonacci.py script that asserts the output of fibonacci(10) is 55",
      "dependencies": ["T1"],
      "assignee": "Worker"
    }
  ]
}
""",
                # Worker queries
                "Create the fibonacci.py script": """
Reasoning: I will implement an efficient iterative Fibonacci function in Python.
[FILE: fibonacci.py]
```python
def fibonacci(n: int) -> int:
    \"\"\"Return the nth Fibonacci number iteratively.\"\"\"
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return 0
    if n == 1:
        return 1
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
```
""",
                "Create a test_fibonacci.py script": """
Reasoning: I will write unit tests checking edge cases and the required fibonacci(10) == 55 check.
[FILE: test_fibonacci.py]
```python
from fibonacci import fibonacci

def test_fibonacci():
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(5) == 5
    assert fibonacci(10) == 55
    print("All tests passed successfully!")

if __name__ == "__main__":
    test_fibonacci()
```
""",
                # Reviewer queries
                "Analyze and output the review JSON.": """
{
  "approved": true,
  "feedback": "Perfect implementation. The logic is clean, robust, handles edge cases, and includes structured files."
}
"""
            },
            default_response="Mock agent response completed successfully."
        )
        
    def get_provider(self):
        if self.provider_type == "ollama":
            return self.ollama_provider
        return self.mock_provider

runtime_config = RuntimeConfig()

# Global manager instance
manager = ManagerAgent(provider=runtime_config.get_provider())

class GoalRequest(BaseModel):
    goal: str

class MemoryWriteRequest(BaseModel):
    filename: str
    content: str

class ConfigUpdateRequest(BaseModel):
    provider_type: str
    ollama_host: str | None = None
    default_model: str | None = None

async def run_orchestration_task(goal: str):
    try:
        # Dynamically refresh provider in case configuration was updated
        manager.provider = runtime_config.get_provider()
        await manager.execute_goal(goal)
    except Exception as e:
        logger.error(f"Error executing goal in background: {e}")

@app.post("/api/goals")
async def start_goal(request: GoalRequest, background_tasks: BackgroundTasks):
    if manager.is_running:
        raise HTTPException(status_code=400, detail="Orchestration is already running.")
    
    background_tasks.add_task(run_orchestration_task, request.goal)
    return {"status": "started", "message": "Multi-agent orchestration started in background."}

@app.get("/api/status")
async def get_status():
    tasks_data = manager.memory.load_tasks()
    return {
        "is_running": manager.is_running,
        "logs": manager.logs,
        "tasks": tasks_data.get("tasks", [])
    }

@app.get("/api/memory")
async def get_memory():
    return {
        "project_state.json": manager.memory.load_project_state(),
        "tasks.json": manager.memory.load_tasks(),
        "roadmap.md": manager.memory.read_file("roadmap.md"),
        "decisions.md": manager.memory.read_file("decisions.md"),
        "session_log.md": manager.memory.read_file("session_log.md"),
        "context.md": manager.memory.read_file("context.md"),
    }

@app.post("/api/memory/write")
async def write_memory(request: MemoryWriteRequest):
    valid_files = {"roadmap.md", "decisions.md", "session_log.md", "context.md"}
    if request.filename not in valid_files:
        raise HTTPException(status_code=400, detail=f"Editing of '{request.filename}' is not allowed or unsupported.")
    try:
        manager.memory.write_file(request.filename, request.content)
        return {"status": "success", "message": f"Successfully updated memory file '{request.filename}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
async def get_config():
    return {
        "provider_type": runtime_config.provider_type,
        "ollama_host": runtime_config.ollama_host,
        "default_model": runtime_config.default_model
    }

@app.post("/api/config")
async def update_config(request: ConfigUpdateRequest):
    if request.provider_type not in ["ollama", "mock"]:
        raise HTTPException(status_code=400, detail="Provider type must be 'ollama' or 'mock'")
        
    runtime_config.provider_type = request.provider_type
    if request.ollama_host:
        runtime_config.ollama_host = request.ollama_host
        runtime_config.ollama_provider = OllamaProvider(request.ollama_host)
    if request.default_model:
        runtime_config.default_model = request.default_model
        
    # Re-instantiate/update manager's provider reference
    manager.provider = runtime_config.get_provider()
    
    return {"status": "success", "config": await get_config()}

# Mount Static UI assets at root '/'
ui_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ui"))
if os.path.exists(ui_dir):
    app.mount("/", StaticFiles(directory=ui_dir, html=True), name="ui")
else:
    logger.warning(f"UI directory not found at: {ui_dir}. Frontend will not be served.")
