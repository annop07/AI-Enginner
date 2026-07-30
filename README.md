# AI Agent Service

> **Week 1 Bootcamp deliverable** — a FastAPI microservice running an AI agent that does **structured output**, **tool/function calling**, and **vector similarity search**.

A production-shaped starting point for an AI Engineer portfolio: typed end-to-end,
tested, containerised, and runnable with zero external infrastructure.

## What it demonstrates

| Skill (Week 1) | Where it lives |
| --- | --- |
| Structured Output (Pydantic + Instructor) | [`app/extractor.py`](app/extractor.py), `POST /extract` |
| Tool / Function Calling | [`app/agent.py`](app/agent.py), [`app/tools/`](app/tools/), `POST /chat` |
| Vector DB — Embedding & Similarity Search (Qdrant + fastembed) | [`app/vectorstore.py`](app/vectorstore.py), `POST /knowledge/*` |
| Token / Cost Observability + Dashboard | [`app/usage.py`](app/usage.py), [`app/static/dashboard.html`](app/static/dashboard.html), `GET /dashboard` |

The **agent loop** ([`app/agent.py`](app/agent.py)) lets the LLM decide on its own which
tools to call and when it has enough information to answer — the core idea that separates
"an agent" from "a prompt".

## Architecture

```
HTTP  ──▶  FastAPI (app/main.py)
                │
    ┌───────────┼─────────────────────────┐
    ▼           ▼                          ▼
 /chat       /extract               /knowledge/*
 agent.py    extractor.py           vectorstore.py
    │        (Instructor →           (Qdrant + fastembed
    │         Pydantic schema)        local embeddings)
    ▼
 tool loop ──▶ tools/registry.py ──▶ calculator · get_time · search_knowledge
   (OpenAI function calling)
```

## Tools the agent can call

- **`calculator`** — safe arithmetic (AST-based, no `eval`)
- **`get_time`** — live date/time for any IANA timezone (data the LLM cannot know)
- **`search_knowledge`** — RAG-style lookup against the Qdrant vector store

Adding a tool = one decorated function in [`app/tools/builtins.py`](app/tools/builtins.py).
Its Pydantic argument model becomes the JSON Schema the LLM sees, and the LLM's arguments
are validated against it before the tool runs.

## Project layout

```
AI-Engineer/
  app/            FastAPI backend (the AI engine + API)
  frontend/       Next.js dashboard (TypeScript + Tailwind + shadcn/ui)
  scripts/        seed + demo helpers
  tests/          pytest suite
```

The backend is a pure API; the Next.js app is a separate frontend that calls it
over HTTP. A minimal server-rendered dashboard also lives at `/dashboard` (no
build step) if you just want to peek without running the Next.js app.

## Quick start

### Backend (FastAPI)

```bash
# 1. install deps (uv pulls Python 3.12 itself)
uv sync

# 2. configure
cp .env.example .env
# edit .env → add your OPENAI_API_KEY

# 3. (optional) seed the knowledge base
uv run python -m scripts.seed_knowledge

# 4. run
uv run uvicorn app.main:app --reload
```

Open the interactive docs at **http://localhost:8000/docs**.

### Frontend (Next.js)

With the backend running on port 8000:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**. The API base URL is set in `frontend/.env.local`
(`NEXT_PUBLIC_API_BASE`). CORS for `localhost:3000` is already enabled on the backend.

## Try it

```bash
# Tool calling: the agent picks calculator + get_time on its own
curl -s localhost:8000/chat -H 'content-type: application/json' \
  -d '{"message":"What is 1234 * 17, and what time is it in Bangkok?"}' | jq

# Structured output: free text → validated JSON
curl -s localhost:8000/extract -H 'content-type: application/json' \
  -d '{"text":"Standup with Aon and Beam. Aon to fix the login bug by Friday (high). Beam will draft the release notes."}' | jq

# Similarity search
curl -s localhost:8000/knowledge/search -H 'content-type: application/json' \
  -d '{"query":"when is the office closed?","top_k":2}' | jq
```

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | liveness + config/vector status |
| GET | `/tools` | tool specs exposed to the LLM |
| POST | `/chat` | run the tool-calling agent |
| POST | `/extract` | structured output (Instructor) |
| POST | `/knowledge/seed` | add documents |
| POST | `/knowledge/search` | similarity search |
| GET | `/models` | models the endpoint offers + the default |
| GET | `/usage/summary` | aggregated token stats (JSON) |
| GET | `/dashboard` | live token-usage dashboard (HTML) |

## Switching models

`/chat` and `/extract` accept an optional `model` field; omit it to use `LLM_MODEL`
from `.env`. An id the endpoint doesn't offer is rejected with **400**, and a model
that can't handle tool calling comes back as **422** with a readable message rather
than a raw 500.

```bash
curl -s localhost:8000/chat -H 'content-type: application/json' \
  -d '{"message":"What is 6 * 7?","model":"gemini-3.5-flash-lite"}' | jq
```

The Next.js dashboard has a searchable model picker next to the send button
(grouped by family), and remembers the last pick in `localStorage`. Since every
request records the model that actually served it, the dashboard doubles as a
cheap way to compare models on cost and latency.

## Usage dashboard

Every LLM-backed request (`/chat`, `/extract`) records its token usage
(prompt / completion / total), LLM round-trips, model, and latency into a
SQLite table ([`app/usage.py`](app/usage.py)). Open **http://localhost:8000/dashboard** for:

- summary cards (total requests, tokens, prompt vs completion, avg latency)
- an **"Ask the agent"** box that shows the exact token cost of *that* request
- charts: tokens over time, tokens by model
- a recent-requests table

Because the service is model-agnostic, switching `LLM_MODEL` in `.env` is
reflected automatically — handy for comparing token efficiency across models.

## Vector store modes

- **Embedded (default):** `QDRANT_LOCATION=./data/qdrant` — persistent, no server.
- **Server:** `docker compose up -d`, then `QDRANT_LOCATION=http://localhost:6333`.

Embeddings run **locally** via [fastembed](https://github.com/qdrant/fastembed)
(`BAAI/bge-small-en-v1.5`) — no embeddings API bill.

## Tests

```bash
uv run pytest        # tool registry, validation, and vector search — no API key needed
```

## Docker

```bash
docker build -t ai-agent-service .
docker run -p 8000:8000 --env-file .env ai-agent-service
```

## Tech stack

FastAPI · OpenAI (function calling) · Instructor · Pydantic v2 · Qdrant · fastembed · uv · pytest
