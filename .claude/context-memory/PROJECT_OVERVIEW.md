# Project Overview

## Project Name

**LightRAG** — A BuddyAI backend RAG system with UIT Buddy Backend proxy

## What This Project Is

This project is the **RAG knowledge reasoning engine** for a BuddyAI student assistant chatbot. It provides:
- Document indexing (PDF, TXT, CSV, Markdown)
- Knowledge graph extraction from documents
- Semantic vector search
- LLM-powered question answering grounded in indexed documents
- **Authenticated proxy to UIT Buddy Backend** — forwards user Bearer tokens to get schedules, documents, and user data

It is part of a larger system (`a_guide_to_RAG`) that also includes:
- `demo_rag` — A production RAG pipeline with PostgreSQL + pgvector
- `LightRAG-Claude-Test` — A LightRAG variant with Claude API + SiliconCloud embeddings
- `rag/` — RAG setup guides and documentation

## Core Technology

| Component | Technology |
|---|---|
| RAG Framework | [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG) (`lightrag-hku` pip package) |
| LLM | OpenAI-compatible API (Claude via SiliconCloud-compatible endpoint) |
| Embedding | SiliconCloud (`BAAI/bge-m3` model) |
| Backend Proxy | `httpx` async HTTP client → UIT Buddy Backend (`http://52.64.199.49:8080`) |
| Storage | JSON file-based KV + NanoVectorDB (in-process vector DB) + NetworkX (knowledge graph) |
| Web Framework | FastAPI |
| Language | Python 3.x |

## Project Structure

```
LightRAG/
├── server.py                  # FastAPI entry point — all REST endpoints
├── config.py                  # Environment variables (base URL, timeout, ports)
├── controller/
│   └── BuddyService.py      # Wires endpoints → backend services
├── backend/                   # UIT Buddy Backend HTTP client
│   ├── __init__.py
│   ├── client.py              # UITBuddyClient — shared httpx.AsyncClient wrapper
│   ├── calendar.py            # /api/schedule/deadline, /api/schedule/calendar
│   ├── document.py            # /api/document/folder, search, download
│   └── user.py                # /api/user/me
├── dto/
│   ├── __init__.py
│   ├── ChatRequest.py         # (existing) Pydantic request models
│   └── backend.py             # Pydantic response/request models for UIT Buddy API
├── requirements.txt
└── .claude/
    ├── skills/                # Agent skills (RAG + LightRAG)
    └── context-memory/        # Agent brain docs
```

## Auth Flow

```
User → AI (with Bearer token) → server.py (this project) → UIT Buddy Backend
                                              │
                                              ▼
                                      Extract "Bearer <token>"
                                      Forward as Authorization header
                                              │
                                              ▼
                                      UIT Buddy Backend validates token
                                      Returns user-specific data
                                              │
                                              ▼
                                      server.py proxies response back to AI
```

## REST API Endpoints (Server → AI)

| Method | Path | Forwards To | Purpose |
|---|---|---|---|
| `GET` | `/api/schedule/deadline` | `GET /api/schedule/deadline` | List user deadlines |
| `POST` | `/api/schedule/deadline` | `POST /api/schedule/deadline` | Create a deadline |
| `GET` | `/api/schedule/calendar` | `GET /api/schedule/calendar` | Get semester schedule |
| `GET` | `/api/user/me` | `GET /api/user/me` | Get user profile |
| `GET` | `/api/document/folder` | `GET /api/document/folder` | List folder contents |
| `GET` | `/api/document/search` | `GET /api/document/search` | Search documents |
| `GET` | `/api/document/download/{fileId}` | `GET /api/document/download/{fileId}` | Download file |
| `GET` | `/health` | — | Health check |

## Dependencies

From `requirements.txt`:
- `fastapi>=0.109.0` — Web framework
- `uvicorn[standard]>=0.27.0` — ASGI server
- `httpx>=0.27.0` — Async HTTP client for UIT Buddy Backend
- `pydantic>=2.0.0` — Request/response models
- `python-dotenv>=1.0.0` — .env loading
- `python-multipart>=0.0.9` — File upload

(lightrag-hku and related RAG deps are for the separate LightRAG knowledge engine)

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `UIT_BUDDY_BASE_URL` | `http://52.64.199.49:8080` | UIT Buddy Backend base URL |
| `UIT_BUDDY_TIMEOUT` | `30` | Request timeout in seconds |
| `SERVER_HOST` | `0.0.0.0` | Server bind host |
| `SERVER_PORT` | `8000` | Server port |