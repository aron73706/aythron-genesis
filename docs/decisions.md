# Architecture Decision Records (ADR) Log

This document records the architectural, security, database, and memory decisions made during the design and evolution of Aythron Genesis.

---

## ADR-001: SQLite WAL Mode for Backend State
- **Status**: Approved
- **Context**: Relying on flat JSON files or standard SQLite causes `database is locked` errors during high-concurrency parallel async execution.
- **Decision**: Migrate memory tracking to `aiosqlite` with `PRAGMA journal_mode=WAL;` explicitly enabled.
- **Consequences**: Safely supports highly concurrent reads and writes from multiple agents and web UI SSE streams without blocking.

## ADR-002: RAG Architecture (LanceDB/Chroma + Real-Time Index)
- **Status**: Approved
- **Context**: Custom C-compiled extensions like `sqlite-vec` cause cross-platform installation friction. Furthermore, static RAG indexes become stale immediately when agents write code.
- **Decision**: Use an embedded, easy-to-install vector engine (LanceDB or Chroma). Implement a real-time re-indexing hook that updates vectors on every file write, offloading this CPU-bound task to a `ProcessPoolExecutor`.
- **Consequences**: AI always queries fresh codebase context, preventing hallucinations based on outdated code.

## ADR-003: Scheduler Design with Cascading Failures
- **Status**: Approved
- **Context**: Parallel tasks can fail. If Task A fails, Task B (which depends on A) will deadlock in a pending state forever.
- **Decision**: Implement Kahn's topological sort for cycle detection and introduce explicit cascading failure semantics (aborting downstream tasks if a parent permanently fails).
- **Consequences**: Prevents infinite hanging loops and ensures clean session termination.

## ADR-004: Sandbox Design & Security Mapping
- **Status**: Approved
- **Context**: Running worker code locally poses security risks. Docker provides isolation, but root volume mounts and infinite disk writes cause host OS instability. Network-less docker prevents `pip install`.
- **Decision**: Run ephemeral Docker containers with strict UID mapping (non-root), `--storage-opt size=1G` disk limits, and a pre-built image/proxy to resolve required Python dependencies.
- **Consequences**: Secure, predictable, and functional code verification without risking host compromise or disk exhaustion.

## ADR-005: Memory Strategy & File Locking
- **Status**: Approved
- **Context**: Parallel agents writing to the workspace can corrupt files. Humans editing markdown memory files can have their changes overwritten by DB syncs.
- **Decision**: Implement granular Mutex file-level locking for all workspace writes. Establish bi-directional markdown sync via file watchers.
- **Consequences**: Prevents race conditions and guarantees human developer edits are captured in the DB.

## ADR-006: AI Handoff Continuity Strategy
- **Status**: Approved
- **Context**: New AI assistants or human developers must be able to continue the project without previous conversation history.
- **Decision**: Persist high-level project goals, decisions, and roadmaps exclusively in `docs/` and memory files.
- **Consequences**: Complete state recovery; any LLM can resume development simply by reading the workspace documentation.

## ADR-007: Token Management
- **Status**: Approved
- **Context**: Using OpenAI's `tiktoken` for models like Llama or Qwen results in inaccurate token counts, causing context window overflows.
- **Decision**: Utilize model-specific tokenizers via HuggingFace `transformers` or the native Ollama `/api/tokenize` endpoint.
- **Consequences**: Precise context window management and session budgeting.

## ADR-008: Recovery Strategy
- **Status**: Approved
- **Context**: Hardware failures or server restarts mid-execution must not corrupt the project state.
- **Decision**: The Session Manager will read the SQLite database on boot, identify `running` tasks, and automatically rebuild the async execution graph to resume progress.
- **Consequences**: High resilience and fault tolerance.
