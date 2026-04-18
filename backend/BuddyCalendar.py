"""Calendar & Schedule service — wraps /api/schedule endpoints."""
from __future__ import annotations

from client.BuddyClient import UITBuddyClient
from exception.BuddyException import BackendAPIError

# ---------------------------------------------------------------------------
# Deadlines
# ---------------------------------------------------------------------------

async def get_deadlines(
    client: UITBuddyClient,
    token: str,
    page: int = 1,
    limit: int = 15,
    sortType: str = "desc",
    sortBy: str = "created_at",
    month: int = 1,
    year: int = 1,
) -> dict:
    """
    GET /api/schedule/deadline — list user deadlines.

    Returns the parsed JSON dict from the backend.
    Raises BackendAPIError on non-2xx.
    """
    response = await client.get(
        "/api/schedule/deadline",
        token=token,
        params={
            "page": page,
            "limit": limit,
            "sortType": sortType,
            "sortBy": sortBy,
            "month": month,
            "year": year,
        },
    )
    if not response.is_success:
        raise BackendAPIError(response.status_code, response.text)
    return response.json()


async def create_deadline(
    client: UITBuddyClient,
    token: str,
    exerciseName: str,
    classCode: str,
    dueDate: str,
) -> dict:
    """
    POST /api/schedule/deadline — create a personal deadline.

    Returns the parsed JSON dict from the backend.
    Raises BackendAPIError on non-2xx.
    """
    response = await client.post(
        "/api/schedule/deadline",
        token=token,
        json={
            "exerciseName": exerciseName,
            "classCode": classCode,
            "dueDate": dueDate,
        },
    )
    if not response.is_success:
        raise BackendAPIError(response.status_code, response.text)
    return response.json()


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------

async def get_calendar(
    client: UITBuddyClient,
    token: str,
    year: str = "",
    semester: str = "",
) -> dict:
    """
    GET /api/schedule/calendar — get current-semester course schedule.

    Returns the parsed JSON dict from the backend.
    Raises BackendAPIError on non-2xx.
    """
    response = await client.get(
        "/api/schedule/calendar",
        token=token,
        params={"year": year, "semester": semester},
    )
    if not response.is_success:
        raise BackendAPIError(response.status_code, response.text)
    return response.json()