# Architecture Overview

This project is intentionally built as a single orchestrator first, not as a multi-agent system from day one.

## MVP architecture

The MVP is organized around one central orchestration pipeline:

1. receive the user idea
2. analyze intent
3. generate clarification questions
4. extract requirements
5. propose an architecture
6. generate epics
7. analyze security concerns
8. generate a roadmap
9. return a structured JSON response

## Backend responsibilities

The FastAPI backend is responsible for:

- request validation
- API contract definition
- orchestration entry point
- response shaping with structured outputs
- future LLM provider integration


## Future evolution

The system can evolve toward specialized agents:

- architecture agent
- security agent
- DevOps agent
- product agent
- QA agent



