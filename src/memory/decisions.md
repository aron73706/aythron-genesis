# Architecture Decisions Log

## ADR-001: FastAPI for API Backend and Static Hosting
- **Status**: Approved
- **Date**: 2026-06-12
- **Context**: The application requires an API backend for starting tasks, pulling logs, and updating config, alongside a web UI.
- **Decision**: Use FastAPI to serve both the API endpoints and the static UI assets.
- **Consequences**: Simple setup, single process execution, fast development, and lightweight footprint.

## ADR-002: Vanilla HTML/CSS/JS for UI
- **Status**: Approved
- **Date**: 2026-06-12
- **Context**: We want a clean, fast, and visually spectacular UI without the overhead of heavy JavaScript build steps.
- **Decision**: Use pure HTML, Vanilla CSS, and modern Vanilla ES6 Javascript. Use modern styling like glassmorphism and animations.
- **Consequences**: No Node.js package compilation needed for the final user, highly responsive, and easy to customize.

## ADR-003: Model Abstraction Layer for Ollama
- **Status**: Approved
- **Date**: 2026-06-12
- **Context**: We need to support local models (Qwen, DeepSeek, Llama) with option to extend to cloud models later.
- **Decision**: Implement a generic `LLMProvider` base class and concrete `OllamaProvider`.
- **Consequences**: Code is decoupled from model API specifics. Cloud models can be added by implementing new providers.
