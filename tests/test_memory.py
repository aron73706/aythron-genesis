import os
import shutil
import pytest
from memory.memory_manager import MemoryManager

TEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "temp_test_memory"))

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup
    os.makedirs(TEST_DIR, exist_ok=True)
    yield
    # Teardown
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

def test_json_operations():
    manager = MemoryManager(TEST_DIR)
    
    test_state = {"version": "1.0", "milestone": "Testing"}
    manager.save_project_state(test_state)
    
    loaded = manager.load_project_state()
    assert loaded["version"] == "1.0"
    assert loaded["milestone"] == "Testing"

def test_decision_appends():
    manager = MemoryManager(TEST_DIR)
    
    # Setup initial files
    manager.write_file("decisions.md", "# Architecture Decisions Log\n")
    manager.save_project_state({"architecture_decisions": []})
    
    manager.append_decision(
        title="Test ADR",
        context="Context description",
        decision="Decision made",
        consequences="Consequences details"
    )
    
    decisions_content = manager.read_file("decisions.md")
    assert "ADR-001: Test ADR" in decisions_content
    assert "Decision made" in decisions_content
    
    state = manager.load_project_state()
    assert "ADR-001: Test ADR" in state["architecture_decisions"]

def test_session_log_appends():
    manager = MemoryManager(TEST_DIR)
    
    # Setup initial file
    manager.write_file("session_log.md", "# Session Log\n")
    
    manager.append_session_log(
        activity="Unit Testing",
        outcome="All tests passed",
        next_steps=["Write more tests", "Clean up"]
    )
    
    log_content = manager.read_file("session_log.md")
    assert "Session [" in log_content
    assert "Unit Testing" in log_content
    assert "All tests passed" in log_content
    assert "Write more tests" in log_content
