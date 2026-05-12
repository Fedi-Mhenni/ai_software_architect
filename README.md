# AI Software Architect

AI Software Architect is an engineering orchestrator that turns a rough project idea into a structured software plan.

The goal is not to generate code blindly. The system is designed to think like a senior engineering team and produce actionable outputs such as:

- clarification questions
- requirements extraction
- architecture proposals
- epics and roadmap
- security review
- structured JSON responses

## Why this project exists

When a developer has an idea, the hardest part is often not coding first. The hard part is deciding:

- what to build first
- which architecture fits the idea
- which stack is reasonable
- what security and reliability concerns matter
- how to break the project into coherent steps

This project exists to help with that phase.

## Current MVP

The current backend is a FastAPI service with:

- `GET /health`
- `POST /analyze-project`
- automatic OpenAPI docs at `/docs`
- raw schema at `/openapi.json`

The current implementation returns a temporary structured response while the orchestration pipeline is being built.

## Stack

- Backend: FastAPI
- Server: Uvicorn
- Validation and schemas: Pydantic
- Containerization: Docker / Docker Compose
- Frontend: planned with React or Next.js
- Data store: SQLite for the MVP, later evolutions planned

## Repository structure

- [backend/](backend/) FastAPI backend and launch script
- [ARCHITECTURE.md](ARCHITECTURE.md) architecture decisions and evolution notes
- [ROADMAP.md](ROADMAP.md) delivery phases and future milestones
- [SECURITY.md](SECURITY.md) security guidelines and concerns
- [CONTRIBUTING.md](CONTRIBUTING.md) commit and contribution rules
- [PROMPTS.md](PROMPTS.md) prompt ideas and orchestration notes
- [README.md](README.md) product overview and local run instructions

## Run locally

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Then open:

- `http://localhost:5001/docs`
- `http://localhost:5001/openapi.json`

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the phased MVP and future multi-agent evolution.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [ROADMAP.md](ROADMAP.md)
- [SECURITY.md](SECURITY.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)

