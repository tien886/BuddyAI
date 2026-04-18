---
name: backend-document
description: "Use when the user needs to work with the document service. Examples: 'List user documents', 'Search documents', 'Download a file'"
---

# Backend — Document Service (`backend/document.py`)

## Endpoints

### `GET /api/document/folder`

List contents of a folder (or root folder if `folderId` is empty).

```python
from backend.client import UITBuddyClient
import asyncio

async def main():
    client = UITBuddyClient()
    async with client:
        from backend import document as doc
        result = await doc.get_folder(
            client,
            token="<Bearer token>",
            folderId="",           # empty = root folder
            page=1,
            limit=15,
            sortType="desc",
            sortBy="createdAt",
        )
        print(result)
        # {
        #   "data": [
        #     {"id": "...", "name": "slides.pdf", "fileType": "pdf", "size": 1024000, ...},
        #     ...
        #   ],
        #   "total": 20, "page": 1, "limit": 15
        # }

asyncio.run(main())
```

**Query parameters:**
| Param | Type | Default | Description |
|---|---|---|---|
| `folderId` | str | `""` | Folder ID (empty = root folder) |
| `page` | int | `1` | Page number |
| `limit` | int | `15` | Items per page |
| `sortType` | str | `"desc"` | Sort direction |
| `sortBy` | str | `"createdAt"` | Sort field |

### `GET /api/document/search`

Search accessible documents by keyword.

```python
async with client:
    result = await doc.search_documents(
        client,
        token="<Bearer token>",
        keyword="DevOps",      # search term
        page=1,
        limit=15,
        sortType="desc",
        sortBy="createdAt",
    )
```

**Query parameters:**
| Param | Type | Default | Description |
|---|---|---|---|
| `keyword` | str | `""` | Search term |
| `page` | int | `1` | Page number |
| `limit` | int | `15` | Items per page |
| `sortType` | str | `"desc"` | Sort direction |
| `sortBy` | str | `"createdAt"` | Sort field |

### `GET /api/document/download/{fileId}`

Download a document file as raw bytes.

```python
async with client:
    content = await doc.download_document(
        client,
        token="<Bearer token>",
        fileId="123e4567-e89b-12d3-a456-426614174000",
    )
    # content is raw bytes (PDF, DOCX, TXT, etc.)
    with open("output.pdf", "wb") as f:
        f.write(content)
```

The `fileId` is a UUID string (e.g. `123e4567-e89b-12d3-a456-426614174000`).

**Note:** After downloading, the content can be:
- Passed to `textract` for text extraction → then to `LightRAG.ainsert()` for indexing
- Parsed directly (if text-based)
- Used for document Q&A

## DTO Models

```python
from dto.backend import DocumentItem, DocumentListResponse, DocumentSearchResponse
```

## AI Policy Alignment

According to `AI policies.md`, the AI can:
- `GET /api/document/folder` — read folder contents (if shared with current user)
- `GET /api/document/search` — search accessible documents and answer questions grounded in retrieved results
- `GET /api/document/download/{fileId}` — download file and analyze the content (then index to LightRAG for Q&A)

**Important:** The AI **cannot** access documents not shared with the user. The backend enforces permission.

## Error Cases

- `401 Unauthorized` — missing or invalid Bearer token
- `403 Forbidden` — document not accessible to this user
- `404 Not Found` — document/folder not found
- `5xx` — backend server error

## Workflow: Download → Index to LightRAG

```python
async def download_and_index(client, token, fileId):
    # 1. Download
    content = await doc.download_document(client, token, fileId)

    # 2. Extract text
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    import textract
    text = textract.process(tmp_path).decode("utf-8")

    # 3. Index to LightRAG
    from lightrag import LightRAG
    rag = LightRAG(...)
    await rag.ainsert(text)
```