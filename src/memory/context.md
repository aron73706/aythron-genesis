# System Context & Architecture Guidelines

## Architecture Overview
Aythron Genesis uses an agent hierarchy to orchestrate execution:
- **Manager Agent**: Coordinates the loop, manages state updates, dispatches tasks, and triggers reviews.
- **Planner Agent**: Decomposes goals into a task dependency graph.
- **Worker Agent**: Performs coding or writing tasks.
- **Reviewer Agent**: Validates quality and provides feedback.

The filesystem under `/memory` is the core source of truth. Every run modifies these files to maintain state across agent processes.

## Guidelines for AI Developers
1. **Always Read Memory**: Start any work session by reading files in the `memory/` folder.
2. **Always Write Memory**: When work is completed, update `memory/project_state.json`, `memory/tasks.json`, and `memory/session_log.md` to capture changes.
3. **No Hidden State**: Avoid storing critical decisions in conversations; they must be written to `memory/decisions.md`.
4. **Local First**: Keep dependencies lightweight and support local LLM interfaces (Ollama).
