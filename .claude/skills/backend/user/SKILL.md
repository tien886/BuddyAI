---
name: backend-user
description: "Use when the user needs to get the authenticated user's profile and academic context. Examples: 'Get current user profile', 'Get user credits and GPA'"
---

# Backend — User Service (`backend/user.py`)

## Endpoint

### `GET /api/user/me`

Get the current authenticated user's profile and academic context (credits, grades, major, year, etc.).

```python
from backend.client import UITBuddyClient
import asyncio

async def main():
    client = UITBuddyClient()
    async with client:
        from backend import user as user_svc
        result = await user_svc.get_me(client, token="<Bearer token>")
        print(result)
        # {
        #   "id": "user-uuid",
        #   "name": "Nguyen Van A",
        #   "email": "student@uit.edu.vn",
        #   "studentId": "22512345",
        #   "major": "Computer Science",
        #   "year": "3",
        #   "credits": 90.5,
        #   "gpa": 3.45,
        #   "avatar": "https://..."
        # }

asyncio.run(main())
```

## DTO Model

```python
from dto.backend import UserProfile
```

```python
class UserProfile(BaseModel):
    id: str | None = None
    name: str | None = None
    email: str | None = None
    studentId: str | None = None
    major: str | None = None
    year: str | None = None
    credits: float | None = None
    gpa: float | None = None
    avatar: str | None = None
```

## AI Policy Alignment

According to `AI policies.md`, `GET /api/user/me` retrieves:
- Current user's profile
- Basic academic context (credits, grades, ...)

This data is used by the **Context Builder** to personalize responses:
- "What courses should I take?" → uses `major`, `year`, `credits` to filter recommendations
- "Am I on track to graduate?" → uses `credits`, `gpa` to assess
- "What's my academic standing?" → uses `gpa`, `major` to contextualize

## Error Cases

- `401 Unauthorized` — missing or invalid Bearer token
- `404 Not Found` — user not found in backend
- `5xx` — backend server error

## Usage in BuddyService

```python
async def get_user_profile(self, token: str) -> dict:
    async with self.client:
        return await user_svc.get_me(self.client, token)

# Or via BuddyService singleton
controller = get_buddy_service ()
profile = await controller.get_user_profile(token="Bearer xxx")
```