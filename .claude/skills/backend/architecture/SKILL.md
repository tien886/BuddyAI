---
name: backend-architecture
description: "Use when the user asks how the backend proxy works, how auth is handled, or how to add new backend endpoints. Examples: 'How does the proxy work?', 'How is the Bearer token forwarded?', 'Add a new backend endpoint'"
---

# Backend Proxy — Architecture

## Overview

The `backend/` module is a **typed HTTP client** that forwards authenticated requests from BuddyAI to the UIT Buddy Backend (`http://52.64.199.49:8080`). It is NOT a database — it proxies API calls in real-time.

## Auth Flow

```
AI receives user's Bearer token
         │
         ▼
POST /api/schedule/deadline
Authorization: Bearer <token>
         │
         ▼
server.py extracts token
         │
         ▼
backend/client.py (UITBuddyClient)
  .post("/api/schedule/deadline",
        token="<token>",
        json={...})
         │
         ▼
httpx.AsyncClient GET/POST
Authorization: Bearer <token>
         │
         ▼
UIT Buddy Backend validates token
Returns user-specific data
         │
         ▼
server.py proxies response to AI
```

## UITBuddyClient

```python
from backend.client import UITBuddyClient

client = UITBuddyClient()  # uses config.UIT_BUDDY_BASE_URL, UIT_BUDDY_TIMEOUT

async with client:
    # GET request
    response = await client.get(
        "/api/user/me",
        token="<Bearer token>",
        params={"page": 1},
    )
    data = response.json()

    # POST request
    response = await client.post(
        "/api/schedule/deadline",
        token="<Bearer token>",
        json={"exerciseName": "HW1", "classCode": "NT211", "dueDate": "2026-04-20"},
    )
    data = response.json()

    # File download
    response = await client.download("/api/document/download/{fileId}", token="<token>")
    content_bytes = response.content  # raw bytes
```

## Error Handling

```python
from backend.client import BackendAPIError, UITBuddyClient

client = UITBuddyClient()
async with client:
    try:
        await client.get("/api/user/me", token="bad_token")
    except BackendAPIError as e:
        print(e.status_code)  # 401, 403, 404, 500, etc.
        print(e.detail)       # error message from backend
```

- `BackendAPIError(4xx)` → client's fault (invalid token, bad request) — should be surfaced to AI
- `BackendAPIError(5xx)` → UIT Buddy Backend is down — should be surfaced as server error
- `BackendAPIError(502)` → network error reaching the backend
- `BackendAPIError(504)` → request timed out (after `UIT_BUDDY_TIMEOUT` seconds)

## Adding a New Endpoint

### 1. Add function to the appropriate service file

```python
# backend/calendar.py (or new service file)
async def get_something(
    client: UITBuddyClient,
    token: str,
    param1: str = "",
    page: int = 1,
) -> dict:
    response = await client.get(
        "/api/something/endpoint",
        token=token,
        params={"param1": param1, "page": page},
    )
    if not response.is_success:
        raise BackendAPIError(response.status_code, response.text)
    return response.json()
```

### 2. Add Pydantic model to `dto/backend.py`

```python
class SomethingItem(BaseModel):
    id: str | None = None
    name: str | None = None
    class Config:
        extra = "ignore"

class SomethingResponse(BaseModel):
    data: list[SomethingItem] = Field(default_factory=list)
    total: int | None = None
```

### 3. Add method to BuddyService

```python
async def get_something(self, token: str, param1: str = "", page: int = 1) -> dict:
    async with self.client:
        return await calendar_svc.get_something(self.client, token, param1=param1, page=page)
```

### 4. Add endpoint to server.py

```python
@app.get("/api/something/endpoint")
async def get_something(
        authorization: Annotated[str | None, Header(default=None)] = None,
    param1: str = "",
    page: int = 1,
):
    token = extract_token(authorization)
    try:
        return await get_buddy_service ().get_something(token=token, param1=param1, page=page)
    except BackendAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
```

## Config

| Variable | Default | Source |
|---|---|---|
| `UIT_BUDDY_BASE_URL` | `http://52.64.199.49:8080` | `config.py` |
| `UIT_BUDDY_TIMEOUT` | `30` seconds | `config.py` |

## Key Design Decisions

1. **No token storage** — token is forwarded per-request, never stored
2. **Single AsyncClient** — created once in `async with`, reused across calls to avoid connection overhead
3. **Raw dict responses** — backend services return `dict`, not Pydantic models, to preserve flexibility. Pydantic models live in `dto/backend.py` for type-safe endpoint definitions.
4. **Error propagation** — `BackendAPIError` is raised and caught in `server.py`, converted to `HTTPException`