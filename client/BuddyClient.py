"""Shared HTTP client for the UIT Buddy Backend."""
from __future__ import annotations

import httpx
from config.AppConfig import UIT_BUDDY_BASE_URL, UIT_BUDDY_TIMEOUT
from exception.BuddyException import BackendAPIError



class UITBuddyClient:
    """Async HTTP client that forwards the user's Bearer token to UIT Buddy Backend."""

    def __init__(
        self,
        base_url: str = UIT_BUDDY_BASE_URL,
        timeout: int = UIT_BUDDY_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "UITBuddyClient":
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    async def get(
        self,
        path: str,
        token: str,
        params: dict | None = None,
    ) -> httpx.Response:
        """Make a GET request with the user's token."""
        assert self._client is not None, "Client not started. Use 'async with'."
        try:
            response = await self._client.get(
                path,
                params=params,
                headers=self._headers(token),
            )
            return response
        except httpx.TimeoutException as e:
            raise BackendAPIError(504, f"Request timed out after {self.timeout}s") from e
        except httpx.RequestError as e:
            raise BackendAPIError(502, f"Failed to reach backend: {e}") from e

    async def post(
        self,
        path: str,
        token: str,
        json: dict | None = None,
    ) -> httpx.Response:
        """Make a POST request with the user's token."""
        assert self._client is not None, "Client not started. Use 'async with'."
        try:
            response = await self._client.post(
                path,
                json=json,
                headers=self._headers(token),
            )
            return response
        except httpx.TimeoutException as e:
            raise BackendAPIError(504, f"Request timed out after {self.timeout}s") from e
        except httpx.RequestError as e:
            raise BackendAPIError(502, f"Failed to reach backend: {e}") from e

    async def download(
        self,
        path: str,
        token: str,
    ) -> httpx.Response:
        """Download a file (streaming response) with the user's token."""
        assert self._client is not None, "Client not started. Use 'async with'."
        try:
            response = await self._client.get(
                path,
                headers=self._headers(token),
                follow_redirects=True,
            )
            return response
        except httpx.TimeoutException as e:
            raise BackendAPIError(504, f"Download timed out after {self.timeout}s") from e
        except httpx.RequestError as e:
            raise BackendAPIError(502, f"Failed to reach backend: {e}") from e