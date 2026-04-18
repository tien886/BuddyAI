# BuddyAI Decision Gate

## Purpose

The **Decision Gate** is the critical routing layer that determines how BuddyAI handles every user request. It sits at the entry point of the system and decides the cheapest viable execution path.

**Design principle:** Only activate heavy components (LightRAG, n8n, LLM) when necessary. The system should be fast for simple questions and thorough for complex ones.

## Decision Tree

```
User Request
    │
    ▼
┌──────────────────────┐
│   DOMAIN CHECK       │
│ Is the question      │
│ relevant to BuddyAI? │
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
[In-Domain]  [Out-of-Domain]
     │           │
     │           ▼
     │    skip_all
     │    • No backend
     │    • No LightRAG
     │    • No n8n
     │    • Direct response
     │           │
     └─────┬─────┘
           ▼
┌──────────────────────────┐
│  COMPLEXITY CHECK        │
│ Classify into:           │
│ • Fast                  │
│ • Lookup                │
│ • Thinking              │
└──────────┬─────────────┘
           │
     ┌─────┼──────┐
     ▼     ▼      ▼
  [Fast] [Lookup] [Thinking]
     │     │        │
     │     │        ▼
     │     │   ┌─────────────────────────────┐
     │     │   │ FULL PIPELINE               │
     │     │   │ • Validate Access           │
     │     │   │ • Backend Proxy (Lookup)    │
     │     │   │ • LightRAG (knowledge)      │
     │     │   │ • Context Builder           │
     │     │   │ • n8n Workflow              │
     │     │   │ • LLM (Gemini)              │
     │     │   └─────────────────────────────┘
     │     │              │
     │     ▼              ▼
     │  [Lookup Path]  [Thinking Path]
     │  • Backend Proxy   • Full pipeline
     │  • LightRAG        • n8n + LLM
     │  • no n8n          • Context Builder
     └────────┬──────────────────┘
              │
              ▼
         Response
```

## Step 1 — Domain Check

### In-Domain Topics

- Courses (NT211, CS321, etc.)
- Schedules (class times, exam schedules)
- Deadlines (homework, projects, registration)
- Academic planning (semester planning, course selection)
- Career-related study paths (DevOps, Data Science tracks)
- Prerequisites (what courses need to be taken before another)
- Documents (shared with the user)
- Personal study data (grades, credits, enrolled courses)

### Out-of-Domain Topics

- Weather
- News
- General knowledge unrelated to UIT/courses
- Sports, entertainment, etc.

**Action for out-of-domain:** Return a direct response, skip all backend processing.

```json
{
  "mode": "out_of_domain",
  "action": "skip_all"
}
```

## Step 2 — Complexity Classification

### Fast Path

**Criteria:** No external data needed, no reasoning required.

**Examples:**
- "Hello!" / "Hi there!"
- "Summarize this text for me" (text provided in request)
- "Thanks" / "Goodbye"

**Action:** Answer directly from the question alone.
**Components triggered:** None
**Response time:** Instant

### Lookup Path

**Criteria:** Requires retrieving facts from backend or knowledge base, no multi-step reasoning.

**Examples:**
- "What is NT211?"
- "What deadlines do I have today?"
- "What is my schedule for tomorrow?"
- "Who teaches CS321?"
- "What are the prerequisites for NT548?"
- "Show me my documents"
- "What are my semester courses?"

**Action:** Query Backend Proxy (UIT Buddy) OR LightRAG (or both).
**Components triggered:** Backend Proxy (UIT Buddy Backend via `backend/` services) OR LightRAG (naive/local)
**n8n:** Not triggered
**Response time:** Fast (single retrieval)

**Backend Proxy calls for Lookup:**
- `GET /api/schedule/deadline` — "What deadlines do I have?"
- `GET /api/schedule/calendar` — "What's my schedule tomorrow?"
- `GET /api/user/me` — "What are my current courses / credits?"
- `GET /api/document/search` — "Find me documents about X"

### Thinking Path

**Criteria:** Requires reasoning, planning, or recommendation.

**Examples:**
- "Recommend courses for a DevOps career path"
- "Compare NT211 vs NT212 — which should I take first?"
- "Plan my semester to prepare for DevOps"
- "What skills do I need to be a Data Engineer?"
- "Should I take NT301 or CS321 this semester?"

**Action:** Trigger full pipeline.
**Components triggered:** Backend Proxy + LightRAG (hybrid/mix) + Context Builder + n8n + LLM
**Response time:** Slower (full pipeline)

## Backend Proxy Services (Lookup + Thinking)

The server exposes `backend/` services that forward authenticated requests to UIT Buddy Backend:

```
Backend Proxy → UIT Buddy Backend (52.64.199.49:8080)
    │
    ├─ backend/calendar.py
    │     GET  /api/schedule/deadline    → "my deadlines"
    │     POST /api/schedule/deadline    → "create a deadline"
    │     GET  /api/schedule/calendar    → "my schedule"
    │
    ├─ backend/user.py
    │     GET  /api/user/me              → "my profile / credits"
    │
    └─ backend/document.py
          GET  /api/document/folder      → "my folders"
          GET  /api/document/search     → "search my documents"
          GET  /api/document/download/{id} → "download file"
```

All calls forward the user's Bearer token: `Authorization: Bearer <token>`.

## Key Design Principles

1. **Cheap paths first** — Priority: fast → lookup → thinking
2. **n8n only for thinking** — Avoid over-triggering n8n workflows
3. **Domain awareness is critical** — Out-of-domain questions must not trigger any backend
4. **Separate concerns** — Each layer has one clear responsibility
5. **Grounded responses** — LLM answers only from retrieved context, never hallucinate