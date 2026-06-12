# Aythron Genesis: Project Roadmap

This document outlines the version milestones, feature goals, and long-term vision for the Aythron Genesis multi-agent orchestration platform.

---

## 1. Versioning & Current Status
- **Current Version**: `0.1.0-alpha`
- **Current Focus**: Finalizing Core Architecture and Execution Engine.

---

## 2. Planned Milestones

### Phase 1: Core Foundation & Memory
- [ ] Implement robust Memory Engine with bi-directional markdown sync.
- [ ] Deploy asynchronous SQLite Backend configured in WAL mode.
- [ ] Establish AI Handoff Engine for seamless continuity and context resumption.

### Phase 2: Agent Definitions & Providers
- [ ] Finalize Ollama Provider integration with accurate, model-specific tokenization.
- [ ] Implement the base Worker System with file-level mutex locking.
- [ ] Implement the Planner Agent to decompose goals into JSON schemas.

### Phase 3: Execution & Scheduling
- [ ] Build the Topological Scheduler with Kahn's algorithm and cascading failure handling.
- [ ] Implement the Reviewer Agent for quality checking deliverables.
- [ ] Deploy the Sandbox Execution Environment using Docker with strict UID mapping, disk limits, and dependency proxying.

### Phase 4: UI & Deployment
- [ ] Develop the Web UI (Glassmorphic SPA) connected via HTTP/SSE.
- [ ] Create robust Docker Deployment profiles (`docker-compose.yml`) for instant out-of-the-box usage.

### Phase 5: Finalization
- [ ] Comprehensive testing and security auditing.
- [ ] Official Public Release to GitHub.
