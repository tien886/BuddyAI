"""User service — wraps /api/user endpoints."""
from __future__ import annotations

from client.BuddyClient import UITBuddyClient
from exception.BuddyException import BackendAPIError


async def get_me(client: UITBuddyClient, token: str) -> dict:
    """
    GET /api/user/me — get current user's profile and academic context.

    Returns the parsed JSON dict from the backend.
    Raises BackendAPIError on non-2xx.
    """
    response = await client.get("/api/user/me", token=token)
    if not response.is_success:
        raise BackendAPIError(response.status_code, response.text)
    return response.json()