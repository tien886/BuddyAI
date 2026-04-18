---
name: backend-calendar
description: "Use when the user needs to work with the calendar/schedule service. Examples: 'Get user deadlines', 'Create a deadline', 'Get semester calendar'"
---

# Backend — Calendar Service (`backend/calendar.py`)

## Endpoints

### `GET /api/schedule/deadline`

List user's deadlines (upcoming, overdue, completed).

```python
from backend.client import UITBuddyClient
import asyncio

async def main():
    client = UITBuddyClient()
    async with client:
        from backend import calendar as cal
        result = await cal.get_deadlines(
            client,
            token="<Bearer token>",
            page=1,
            limit=15,
            sortType="desc",
            sortBy="created_at",
            month=4,    # April
            year=2026,
        )
        print(result)
        # {
        #   "data": [
        #     {"id": "...", "exerciseName": "HW1", "classCode": "NT211", "dueDate": "2026-04-20", ...},
        #     ...
        #   ],
        #   "total": 10, "page": 1, "limit": 15
        # }

asyncio.run(main())
```

**Query parameters:**
| Param | Type | Default | Description |
|---|---|---|---|
| `page` | int | `1` | Page number |
| `limit` | int | `15` | Items per page |
| `sortType` | str | `"desc"` | Sort direction (`asc` or `desc`) |
| `sortBy` | str | `"created_at"` | Sort field |
| `month` | int | `1` | Filter by month (1-12, 1 = all months) |
| `year` | int | `1` | Filter by year (1 = all years) |

### `POST /api/schedule/deadline`

Create a personal deadline from natural language or structured data.

```python
async with client:
    result = await cal.create_deadline(
        client,
        token="<Bearer token>",
        exerciseName="Homework 1",
        classCode="NT211",
        dueDate="2026-04-20",  # ISO date string
    )
```

**Request body:**
| Field | Type | Required | Description |
|---|---|---|---|
| `exerciseName` | str | Yes | Name of the assignment/deadline |
| `classCode` | str | Yes | Course code (e.g. "NT211") |
| `dueDate` | str | Yes | ISO date string (e.g. "2026-04-20") |

### `GET /api/schedule/calendar`

Get current-semester course and schedule information.

```python
async with client:
    result = await cal.get_calendar(
        client,
        token="<Bearer token>",
        year="2026",       # empty string = current year
        semester="1",      # empty string = current semester
    )
```

**Query parameters:**
| Param | Type | Default | Description |
|---|---|---|---|
| `year` | str | `""` | Academic year (empty = auto-detect) |
| `semester` | str | `""` | Semester number (empty = auto-detect) |

## DTO Models

```python
from dto.backend import DeadlineItem, DeadlineListResponse, DeadlineCreateRequest, CalendarItem, CalendarResponse
```

## AI Policy Alignment

According to `AI policies.md`, the AI can:
- `GET /api/schedule/deadline` — answer questions about user's upcoming, overdue, or completed deadlines
- `POST /api/schedule/deadline` — create personal deadlines from natural language requests
- `GET /api/schedule/calendar` — retrieve current-semester course and schedule information to support academic Q&A

## Error Cases

- `401 Unauthorized` — missing or invalid Bearer token
- `403 Forbidden` — token valid but no access to this resource
- `404 Not Found` — no deadlines/schedule found
- `5xx` — backend server error