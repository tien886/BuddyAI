# Architecture

## High-Level System Diagram

```
User Query
    │
    ▼
┌─────────────────────────────┐
│   BuddyAI Decision Gate    │  ← Is question in-domain? Fast / Lookup / Thinking?
└────────────┬──────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
[Fast]            [Lookup/Thinking]
    │                 │
    ▼                 ▼
Direct          ┌─────────────────┐
Response        │  LightRAG Engine │
                └────────┬────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌──────────────┐
    │ VectorDB │  │ KV Store │  │ Graph Storage│
    │(NanoVec) │  │  (JSON)  │  │  (NetworkX)  │
    └──────────┘  └──────────┘  └──────────────┘
                         │
                         ▼
                ┌─────────────────────┐
                │  UIT Buddy Backend  │
                │  (52.64.199.49)     │
                │  via httpx client   │
                │  Bearer token fwd   │
                └──────────┬──────────┘
                           │
                ┌──────────┴──────────┐
                │  Backend Services   │
                │ calendar / document  │
                │ / user              │
                └─────────────────────┘
                         │
                         ▼
                   Answer Response
```

## FastAPI Server Architecture

```
server.py (FastAPI)
├── /api/schedule/deadline    GET  → BuddyService → backend/calendar.py
├── /api/schedule/deadline    POST → BuddyService → backend/calendar.py
├── /api/schedule/calendar    GET  → BuddyService → backend/calendar.py
├── /api/user/me              GET  → BuddyService → backend/user.py
├── /api/document/folder      GET  → BuddyService → backend/document.py
├── /api/document/search      GET  → BuddyService → backend/document.py
├── /api/document/download/{fileId} GET → BuddyService → backend/document.py
└── /health                   GET  → {"status": "ok"}

Backend Proxy Flow:
  Header: Authorization: Bearer <token>
       │
       ▼
  backend/client.py (UITBuddyClient)
  ├── get() → httpx.AsyncClient GET
  ├── post() → httpx.AsyncClient POST
  └── download() → httpx.AsyncClient GET (streaming)
       │
       ▼
  UIT Buddy Backend (52.64.199.49:8080)
```

## Backend Module Structure

```
backend/
├── client.py       # UITBuddyClient — shared httpx wrapper
│                   # Methods: get(), post(), download()
│                   # Auth: adds Authorization: Bearer <token>
│                   # Error: BackendAPIError on non-2xx
├── calendar.py     # get_deadlines(), create_deadline(), get_calendar()
├── document.py     # get_folder(), search_documents(), download_document()
└── user.py         # get_me()
```

## Component Responsibilities

| Layer | Responsibility | Triggered In |
|---|---|---|
| **Decision Gate** | Route question to correct path | Always |
| **Backend Proxy** | Forward authenticated requests to UIT Buddy Backend | Lookup + Thinking |
| **backend/calendar** | Get/create deadlines, get semester calendar | Lookup + Thinking |
| **backend/document** | List/search/download documents | Lookup + Thinking |
| **backend/user** | Get authenticated user profile | Lookup + Thinking |
| **LightRAG** | Knowledge graph (course info, policies, prerequisites) | Lookup + Thinking |
| **Context Builder** | Merge + deduplicate backend + KG data | Thinking |
| **n8n** | Orchestration, workflow management | Thinking only |
| **LLM (Gemini)** | Explanation, recommendation, summarization | Thinking only |

## Design Principles

1. **Token forwarding** — No token storage. The AI sends `Authorization: Bearer <token>`, server forwards it unchanged to UIT Buddy.
2. **Async everywhere** — All HTTP calls use `httpx.AsyncClient` with a shared client lifecycle.
3. **Error propagation** — `BackendAPIError` carries the backend's status code and detail for proper HTTP error responses.
4. **Separation of concerns** — `backend/` services are pure HTTP wrappers. `controller/` orchestrates. `server.py` is thin.
5. **Lazy client** — `UITBuddyClient` creates the `httpx.AsyncClient` only when entering the async context (`async with`), so a single client is reused across all calls.