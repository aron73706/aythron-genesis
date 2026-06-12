# Aythron Genesis: System Architecture Specification

This document defines the final production architecture of the Aythron Genesis multi-agent orchestration platform.

---

## 1. System Topology & Flow

Aythron Genesis coordinates multiple local AI models (via Ollama) using an asynchronous, tenant-isolated architecture. The system integrates file-based workspace modifications with transactional SQLite state tracking.

```text
                         +-----------------------+
                         |      Web UI (SPA)     |
                         +-----------+-----------+
                                     | HTTP / SSE
                                     v
                         +-----------+-----------+
                         |   FastAPI App Router  |
                         +-----------+-----------+
                                     |
                                     v
                   +-----------------+-----------------+
                   |  Multi-Project Session Manager    |
                   +-------+-------------------+-------+
                           |                   |
                           v                   v
                +----------+----------+     +--+------------------+
                |   SQLite DB Backend |     | RAG Vector Store    |
                |   (WAL Mode)        |     | (LanceDB / Chroma)  |
                +---------------------+     +---------------------+
                           |                   |
                           +---------+---------+
                                     |
                                     v
                        +------------+------------+
                        |  Task Scheduler / Loop  |
                        |  (Topological Async)    |
                        +------------+------------+
                                     |
                                     v
                      +--------------+--------------+
                      |   Base Agent & Provider     |
                      |   (Token & Model Router)    |
                      +-------+--------------+------+
                              |              |
                              v              v
                        +-----+----+   +-----+----+
                        | Planner  |   | Reviewer |
                        +----------+   +----------+
                              |
                              v
                        +-----+----+
                        |  Worker  |
                        +-----+----+
                              |
                              v
                   +----------+----------+
                   |  Sandboxed Sandbox  |
                   |  (Docker Runner)    |
                   +---------------------+
```

---

## 2. Multi-Tenant Database Memory Schema

To resolve block concurrency and I/O latency, the memory system utilizes a transactional SQLite database backend configured in **WAL (Write-Ahead Logging) mode** (`PRAGMA journal_mode=WAL;`). This prevents `database is locked` errors during high-concurrency async operations.

### Multi-Project Isolation
The `projects` table ensures logical multi-tenancy. Workspaces are strictly separated, allowing multiple independent projects to run simultaneously on the same host.

### Session Recovery
If the server crashes or restarts, the `sessions` and `tasks` tables maintain the exact execution state. On startup, the Session Manager identifies `running` tasks, re-evaluates the dependency graph, and resumes execution without losing progress.

### Tables Overview
- **users**: Authorized developers.
- **projects**: Multi-project isolation paths.
- **sessions**: Goal execution context.
- **tasks**: Graph of tasks and dependencies.
- **decisions / audit_logs**: History and architectural records.

---

## 3. RAG Semantic Context Engine & CPU Offloading

1. **Workspace Syncing**: Codebase files are parsed and converted to vector embeddings using an embedded vector store (e.g., LanceDB or Chroma). 
2. **CPU-Bound Offloading**: All heavy chunking and embedding operations are wrapped in `asyncio.to_thread()` or a `ProcessPoolExecutor` to ensure the FastAPI async event loop is never blocked.
3. **Real-Time Re-Indexing**: The memory system hooks into file write operations. When an agent modifies a file, the vector store dynamically deletes the old chunks and re-embeds the new file content in real-time.
4. **Dynamic Injection**: The `RAGManager` runs semantic searches with the task description, pulling the top-5 relevant snippets as prompt context.

---

## 4. Workspace Concurrency & AI Handoff

### File-Level Locking
To prevent race conditions when parallel workers write to the filesystem, a **Granular File Locking mechanism** (Mutex per file path) is enforced. Two agents cannot write to the same file simultaneously.

### AI Handoff Continuity
Memory files (`decisions.md`, `roadmap.md`) act as the absolute source of truth. A **Bi-Directional Sync** mechanism (via file watchers) ensures that if a human developer manually edits these markdown files, the changes are immediately synced back to the SQLite DB, preserving context for future AI handoffs.

---

## 5. Topological Parallel Task Scheduler

The `Scheduler` resolves task execution order asynchronously:
- **Dependency Validation**: Runs Kahn's algorithm (topological sort) on planner output to check for cycles.
- **Async Gathering**: Dispatches eligible tasks simultaneously using a concurrency throttle (`asyncio.Semaphore`).
- **Cascading Failure Handling**: If a parent task fails permanently (exhausting max attempts), the scheduler automatically triggers a cascading abort, marking all downstream dependent children as `aborted` to prevent deadlocks.

---

## 6. Sandboxed Code Execution Engine

To mitigate host code execution vulnerabilities:
- **Execution Sandbox**: Worker code validation runs inside an ephemeral Docker container.
- **User Permission Mapping**: Sandbox mounts run with strict User ID (UID) mappings to prevent root-owned file generation on the host.
- **Resource Constraints**: Capped at `512m` memory, `512` CPU shares, and a strict `--storage-opt size=1G` to prevent disk exhaustion denial-of-service.
- **Dependency Proxy**: Provides a restricted proxy or a pre-built data-science base image, allowing the isolated network to resolve valid `pip install` requests before blocking all other outbound traffic.

---

## 7. Token Budgeting & Cost Safeguards

The base agent strictly enforces token limits:
- **Accurate Tokenization**: Replaces generic Tiktoken with HuggingFace `transformers` or Ollama's native `/api/tokenize` endpoint to accurately count BPE tokens for the specific local model in use (e.g., Llama 3, Qwen).
- **Budget Tracking**: Session-level `token_budget` is tracked. If `tokens_consumed` exceeds the limit, the loop aborts gracefully.
