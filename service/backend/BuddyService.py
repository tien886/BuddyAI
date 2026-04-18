"""BuddyService — wires FastAPI endpoints to UIT Buddy Backend services."""
from __future__ import annotations

from backend import BuddyCalendar as calendar_svc
from backend import BuddyDocument as document_svc
from backend import BuddyUser as user_svc
from client.BuddyClient import UITBuddyClient


class BuddyService:
    """Thin async wrapper around UIT Buddy Backend services."""

    def __init__(self):
        self.client = UITBuddyClient()

    async def get_deadlines(
        self,
        token: str,
        page: int = 1,
        limit: int = 15,
        sortType: str = "desc",
        sortBy: str = "created_at",
        month: int = 1,
        year: int = 1,
    ) -> dict:
        async with self.client:
            return await calendar_svc.get_deadlines(
                self.client, token,
                page=page, limit=limit,
                sortType=sortType, sortBy=sortBy,
                month=month, year=year,
            )

    async def create_deadline(
        self,
        token: str,
        exerciseName: str,
        classCode: str,
        dueDate: str,
    ) -> dict:
        async with self.client:
            return await calendar_svc.create_deadline(
                self.client, token,
                exerciseName=exerciseName,
                classCode=classCode,
                dueDate=dueDate,
            )

    async def get_calendar(
        self,
        token: str,
        year: str = "",
        semester: str = "",
    ) -> dict:
        async with self.client:
            return await calendar_svc.get_calendar(
                self.client, token,
                year=year, semester=semester,
            )

    async def get_user_profile(self, token: str) -> dict:
        async with self.client:
            return await user_svc.get_me(self.client, token)

    async def get_folder(
        self,
        token: str,
        folderId: str = "",
        page: int = 1,
        limit: int = 15,
        sortType: str = "desc",
        sortBy: str = "createdAt",
    ) -> dict:
        async with self.client:
            return await document_svc.get_folder(
                self.client, token,
                folderId=folderId,
                page=page, limit=limit,
                sortType=sortType, sortBy=sortBy,
            )

    async def search_documents(
        self,
        token: str,
        keyword: str = "",
        page: int = 1,
        limit: int = 15,
        sortType: str = "desc",
        sortBy: str = "createdAt",
    ) -> dict:
        async with self.client:
            return await document_svc.search_documents(
                self.client, token,
                keyword=keyword,
                page=page, limit=limit,
                sortType=sortType, sortBy=sortBy,
            )

    async def download_document(self, token: str, fileId: str) -> bytes:
        async with self.client:
            return await document_svc.download_document(
                self.client, token, fileId
            )


# Singleton instance shared across endpoints
_buddy_service: BuddyService | None = None


def get_buddy_service () -> BuddyService:
    global _buddy_service
    if _buddy_service is None:
        _buddy_service = BuddyService()
    return _buddy_service
