import os
import shutil
import pytest
import json
from agents.provider import MockProvider
from planner.planner import PlannerAgent
from workers.worker import WorkerAgent
from reviewer.reviewer import ReviewerAgent
from agents.manager import ManagerAgent

TEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "temp_test_agents"))

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup
    os.makedirs(TEST_DIR, exist_ok=True)
    
    # Pre-populate memory files needed for manager
    memory_dir = os.path.join(TEST_DIR, "memory")
    os.makedirs(memory_dir, exist_ok=True)
    
    with open(os.path.join(memory_dir, "context.md"), "w") as f:
        f.write("# Test Context")
    with open(os.path.join(memory_dir, "project_state.json"), "w") as f:
        json.dump({"completed_features": []}, f)
    with open(os.path.join(memory_dir, "roadmap.md"), "w") as f:
        f.write("# Roadmap")
    with open(os.path.join(memory_dir, "decisions.md"), "w") as f:
        f.write("# Decisions")
    with open(os.path.join(memory_dir, "session_log.md"), "w") as f:
        f.write("# Sessions")
    with open(os.path.join(memory_dir, "tasks.json"), "w") as f:
        json.dump({"tasks": []}, f)
        
    yield
    # Teardown
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

@pytest.mark.asyncio
async def test_planner():
    provider = MockProvider(
        default_response="""
{
  "tasks": [
    {
      "id": "T1",
      "description": "Task 1",
      "dependencies": [],
      "assignee": "Worker"
    }
  ]
}
"""
    )
    planner = PlannerAgent(provider, "test-model")
    plan = await planner.create_plan("Build something", "Context info")
    
    assert "tasks" in plan
    assert plan["tasks"][0]["id"] == "T1"

@pytest.mark.asyncio
async def test_reviewer():
    provider = MockProvider(
        default_response='{"approved": true, "feedback": "Nice job"}'
    )
    reviewer = ReviewerAgent(provider, "test-model")
    review = await reviewer.review_work("Task description", "Worker output", "Context")
    
    assert review["approved"] is True
    assert review["feedback"] == "Nice job"

@pytest.mark.asyncio
async def test_manager_loop():
    # Setup mock responses for complete loop
    response_map = {
        "Generate the task list in JSON format": """
{
  "tasks": [
    {
      "id": "T1",
      "description": "Create testfile.txt with content 'Hello'",
      "dependencies": [],
      "assignee": "Worker"
    }
  ]
}
""",
        "Create testfile.txt": """
Reasoning: Creating file.
[FILE: testfile.txt]
```
Hello World
```
""",
        "Analyze and output the review JSON.": '{"approved": true, "feedback": "Correct file contents"}'
    }
    
    provider = MockProvider(response_map=response_map)
    manager = ManagerAgent(provider)
    # Override workspace directory to our temp test dir
    manager.memory.workspace_dir = TEST_DIR
    manager.memory.memory_dir = os.path.join(TEST_DIR, "memory")
    
    success = await manager.execute_goal("Create a test file")
    
    assert success is True
    
    # Check that file testfile.txt was created inside workspace dir
    written_file_path = os.path.join(TEST_DIR, "testfile.txt")
    assert os.path.exists(written_file_path)
    with open(written_file_path, "r") as f:
        assert f.read().strip() == "Hello World"
        
    # Check tasks.json was updated to completed
    tasks_data = manager.memory.load_tasks()
    assert tasks_data["tasks"][0]["status"] == "completed"
