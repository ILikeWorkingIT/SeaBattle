# Sea Battle

Desktop PvE Battleship: a human player vs a server-side heatmap bot. Engineering sample of DDD / Clean Architecture, REST + WebSocket, PySide6 client, FastAPI + Redis, Docker Compose.

**Not a production SaaS.** No login, no PvP, no manual ship placement. Frozen MVP: git tag **v1.0.0** (branch `main`).

## Stack

Python 3.12+, FastAPI, Redis 7, PySide6, pytest. API: `http://localhost:8000`.

## Architecture (one glance)

Player → desktop UI (host process) → FastAPI (`backend` container, port 8000) → Redis (sessions with idle TTL, registry of max 3 slots, statistics HASH+LIST). Shots and surrender go over WebSocket `/sessions/{id}/ws`. Heatmap never leaves the server.

Portfolio write-up (Russian): [artifacts/portfolio/](artifacts/portfolio/). C4 diagrams: [diagrams/diagram-c4-001.md](diagrams/diagram-c4-001.md).

## Run

API (from repo root, your machine — not the Cursor agent terminal):

```powershell
docker compose up --build
```

Redis files default to `F:/Docker/Redis` on the host. Another disk or folder: set `REDIS_DATA_DIR` in `.env` (see `.env.example`).

Desktop window: double-click `src/run-frontend.bat`, or:

```powershell
cd src
$env:PYTHONPATH = (Get-Location).Path
python -m frontend
```

OpenAPI YAML: `requirements/openapi.yaml`. Swagger preview script: `requirements/run-openapi-docs.bat` (ports 8080/8081). Live Try it out needs the Compose backend on 8000.

Full “clone on another PC, no Cursor” walkthrough (Russian): [reports/instruction.md](reports/instruction.md). License: [MIT](LICENSE).

## Requirements pack

Functional/non-functional tables, user stories, Cockburn use cases, domain model, data dictionary, closed decisions `Axxxx`: folder `requirements/`.
