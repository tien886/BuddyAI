"""Document service — wraps /api/document endpoints."""
from __future__ import annotations

from client.BuddyClient import UITBuddyClient
from exception.BuddyException import BackendAPIError

async def get_folder(
    client: UITBuddyClient,
    token: str,
    folderId: str = "",
    page: int = 1,
    limit: int = 15,
    sortType: str = "desc",
    sortBy: str = "createdAt",
) -> dict:
    """
    GET /api/document/folder — list folder contents.

    Returns the parsed JSON dict from the backend.
    Raises BackendAPIError on non-2xx.
    """
    response = await client.get(
        "/api/document/folder",
        token=token,
        params={
            "folderId": folderId,
            "page": page,
            "limit": limit,
            "sortType": sortType,
            "sortBy": sortBy,
        },
    )
    if not response.is_success:
        raise BackendAPIError(response.status_code, response.text)
    return response.json()


async def search_documents(
    client: UITBuddyClient,
    token: str,
    keyword: str = "",
    page: int = 1,
    limit: int = 15,
    sortType: str = "desc",
    sortBy: str = "createdAt",
) -> dict:
    """
    GET /api/document/search — search accessible documents.

    Returns the parsed JSON dict from the backend.
    Raises BackendAPIError on non-2xx.
    """
    response = await client.get(
        "/api/document/search",
        token=token,
        params={
            "keyword": keyword,
            "page": page,
            "limit": limit,
            "sortType": sortType,
            "sortBy": sortBy,
        },
    )
    if not response.is_success:
        raise BackendAPIError(response.status_code, response.text)
    return response.json()


async def download_document(
    client: UITBuddyClient,
    token: str,
    fileId: str,
) -> bytes:
    """
    GET /api/document/download/{fileId} — download file content.

    Returns raw bytes of the file.
    Raises BackendAPIError on non-2xx.
    """
    response = await client.download(
        f"/api/document/download/{fileId}",
        token=token,
    )
    if not response.is_success:
        raise BackendAPIError(response.status_code, response.text)
    return response.content