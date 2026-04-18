"""FastAPI server — exposes UIT Buddy Backend APIs to BuddyAI."""
from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from config.AppConfig import SERVER_HOST, SERVER_PORT
from service.backend.BuddyService import get_buddy_service 
from client.BuddyClient import UITBuddyClient
from exception.BuddyException import BackendAPIError
app = FastAPI(
    title="BuddyAI — UIT Buddy Backend Proxy",
    description="Proxies authenticated requests to UIT Buddy Backend for BuddyAI.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def validate_token(authorization: str) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.strip()

    parts = token.split(".")

    if len(parts) != 3:
        raise HTTPException(
            status_code=401,
            detail="Invalid token format (expected JWT with 3 parts)"
        )

    return token


# ---------------------------------------------------------------------------
# /schedule — deadlines & calendar
# ---------------------------------------------------------------------------

@app.get("/api/schedule/deadline")
async def get_deadlines(
    authorization: str ,
    page: int = 1,
    limit: int = 15,
    sortType: str = "desc",
    sortBy: str = "created_at",
    month: int = 1,
    year: int = 1,
):
    print(authorization)
    token = validate_token(authorization)
    try:
        return await get_buddy_service ().get_deadlines(
            token=token,
            page=page,
            limit=limit,
            sortType=sortType,
            sortBy=sortBy,
            month=month,
            year=year,
        )
    except BackendAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@app.post("/api/schedule/deadline")
async def create_deadline(
    authorization: str,
    exerciseName: str = "",
    classCode: str = "",
    dueDate: str = "",
):
    token = validate_token(authorization)
    try:
        return await get_buddy_service ().create_deadline(
            token=token,
            exerciseName=exerciseName,
            classCode=classCode,
            dueDate=dueDate,
        )
    except BackendAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@app.get("/api/schedule/calendar")
async def get_calendar(
    authorization: str,
    year: str = "",
    semester: str = "",
):
    token = validate_token(authorization)
    try:
        return await get_buddy_service ().get_calendar(
            token=token,
            year=year,
            semester=semester,
        )
    except BackendAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


# ---------------------------------------------------------------------------
# /user
# ---------------------------------------------------------------------------

@app.get("/api/user/me")
async def get_user_me(
    authorization: str,
):
    token = validate_token(authorization)
    try:
        return await get_buddy_service ().get_user_profile(token=token)
    except BackendAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


# ---------------------------------------------------------------------------
# /document
# ---------------------------------------------------------------------------

@app.get("/api/document/folder")
async def get_folder(
    authorization: str,
    folderId: str = "",
    page: int = 1,
    limit: int = 15,
    sortType: str = "desc",
    sortBy: str = "createdAt",
):
    token = validate_token(authorization)
    try:
        return await get_buddy_service ().get_folder(
            token=token,
            folderId=folderId,
            page=page,
            limit=limit,
            sortType=sortType,
            sortBy=sortBy,
        )
    except BackendAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@app.get("/api/document/search")
async def search_documents(
    authorization: str ,
    keyword: str = "",
    page: int = 1,
    limit: int = 15,
    sortType: str = "desc",
    sortBy: str = "createdAt",
):
    token = validate_token(authorization)
    try:
        return await get_buddy_service ().search_documents(
            token=token,
            keyword=keyword,
            page=page,
            limit=limit,
            sortType=sortType,
            sortBy=sortBy,
        )
    except BackendAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@app.get("/api/document/download/{fileId}")
async def download_document(
    authorization: str,
    fileId: str = "",
):
    token = validate_token(authorization)
    try:
        content = await get_buddy_service ().download_document(
            token=token,
            fileId=fileId,
        )
        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{fileId}"'},
        )
    except BackendAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    client = UITBuddyClient()
    response = client.get(path="/docs", token=None, params=None)
    if( response is None):
        return {"status": "error", "detail": "Cannot reach UIT Buddy Backend"}
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
