import os
import json
import logging
import datetime
from typing import Any

logger = logging.getLogger("aythron.memory_manager")

class MemoryManager:
    """Manages reading and writing shared memory files in a thread-safe-like atomic manner."""
    
    def __init__(self, workspace_dir: str):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.memory_dir = os.path.join(self.workspace_dir, "memory")
        os.makedirs(self.memory_dir, exist_ok=True)
        
    def _get_path(self, filename: str) -> str:
        return os.path.join(self.memory_dir, filename)
        
    def read_file(self, filename: str) -> str:
        """Reads raw text from a memory file."""
        filepath = self._get_path(filename)
        if not os.path.exists(filepath):
            return ""
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
            
    def write_file(self, filename: str, content: str) -> None:
        """Writes raw text atomically to a memory file."""
        filepath = self._get_path(filename)
        temp_filepath = filepath + ".tmp"
        try:
            with open(temp_filepath, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(temp_filepath, filepath)
        except Exception as e:
            logger.error(f"Failed to write memory file {filename}: {e}")
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            raise

    def load_json(self, filename: str) -> dict[str, Any]:
        """Loads and parses JSON from a memory file."""
        content = self.read_file(filename)
        if not content:
            return {}
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {filename}: {e}")
            return {}
            
    def save_json(self, filename: str, data: dict[str, Any]) -> None:
        """Saves dictionary data as formatted JSON atomically."""
        content = json.dumps(data, indent=2)
        self.write_file(filename, content)
        
    def load_project_state(self) -> dict[str, Any]:
        return self.load_json("project_state.json")
        
    def save_project_state(self, state: dict[str, Any]) -> None:
        self.save_json("project_state.json", state)
        
    def load_tasks(self) -> dict[str, Any]:
        return self.load_json("tasks.json")
        
    def save_tasks(self, tasks: dict[str, Any]) -> None:
        self.save_json("tasks.json", tasks)
        
    def append_decision(self, title: str, context: str, decision: str, consequences: str) -> None:
        """Appends a new architecture decision to decisions.md."""
        date_str = datetime.date.today().isoformat()
        adr_id = sum(1 for line in self.read_file("decisions.md").splitlines() if line.startswith("## ADR-")) + 1
        adr_tag = f"ADR-{adr_id:03d}"
        
        new_adr = f"\n## {adr_tag}: {title}\n"
        new_adr += f"- **Status**: Approved\n"
        new_adr += f"- **Date**: {date_str}\n"
        new_adr += f"- **Context**: {context}\n"
        new_adr += f"- **Decision**: {decision}\n"
        new_adr += f"- **Consequences**: {consequences}\n"
        
        content = self.read_file("decisions.md")
        content += new_adr
        self.write_file("decisions.md", content)
        
        # Also update project_state decisions list
        state = self.load_project_state()
        if "architecture_decisions" not in state:
            state["architecture_decisions"] = []
        state["architecture_decisions"].append(f"{adr_tag}: {title}")
        self.save_project_state(state)

    def append_session_log(self, activity: str, outcome: str, next_steps: list[str]) -> None:
        """Appends a session report to session_log.md."""
        date_str = datetime.date.today().isoformat()
        next_steps_str = "\n".join([f"  - {step}" for step in next_steps])
        
        log_entry = f"\n## Session [{date_str}] - {activity}\n"
        log_entry += f"- **Activity**: {activity}\n"
        log_entry += f"- **Outcome**:\n  - {outcome}\n"
        log_entry += f"- **Next Steps**:\n{next_steps_str}\n"
        
        content = self.read_file("session_log.md")
        content += log_entry
        self.write_file("session_log.md", content)
