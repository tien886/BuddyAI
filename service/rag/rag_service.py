"""service/rag/rag_service.py — orchestrates LightRAG operations.

Mirrors the pattern of service/backend/buddy_service.py.
No FastAPI dependencies here — pure async business logic.
"""
from __future__ import annotations

import json
import asyncio
from rag import (
    query,
    query_context,
    index_documents,
    delete_document,
    get_document_status,
)
from client.rag_client import get_llm_func
from prompts import (
    CHAT_ANSWER_SYSTEM,
    CHAT_ANSWER_USER_TEMPLATE,
    BACKEND_ENDPOINT_PLANNER_SYSTEM,
    BACKEND_ENDPOINT_PLANNER_USER_TEMPLATE,
)
from enum import AuthStatus, BackendEndpoint
from service.backend.buddy_service import get_buddy_service
from exception.buddy.buddy_exception import BackendAPIError
from exception.chat.chat_exception import ChatException
from exception.chat.chat_error_code import ChatErrorCode
from dto import (
    ChatRequest,
    ChatResponse,
    RagQueryRequest,
    RagQueryResponse,
    RagIndexRequest,
    RagIndexResponse,
    RagSeedResponse,
)


class RagService:
    """Thin async wrapper around LightRAG operations."""

    @staticmethod
    def _extract_token(authentication: str) -> str | None:
        """Extract raw JWT token from either 'Bearer <jwt>' or '<jwt>' input."""
        if not authentication:
            return None

        token = authentication.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

        if token.count(".") != 2:
            return None
        return token

    async def _plan_backend_endpoints(self, question: str, has_auth: bool) -> dict:
        llm_func = get_llm_func()
        user_prompt = BACKEND_ENDPOINT_PLANNER_USER_TEMPLATE.format(
            question=question,
            has_auth=str(has_auth).lower(),
        )

        default_plan = {
            "endpoints": [],
            "reasoning": "default backend plan",
        }

        try:
            raw = await llm_func(
                prompt=user_prompt,
                system_prompt=BACKEND_ENDPOINT_PLANNER_SYSTEM,
                history=None,
            )

            data = json.loads(raw.strip())
            print(data)
            endpoints = data.get("endpoints", [])
            if not isinstance(endpoints, list):
                endpoints = []

            allowed = set(BackendEndpoint.values())
            filtered = []

            for ep in endpoints:
                if not isinstance(ep, dict):
                    continue

                name = str(ep.get("name", "")).strip()
                if name not in allowed:
                    continue

                query_params = ep.get("query_params", {})
                body = ep.get("body", {})

                if not isinstance(query_params, dict):
                    query_params = {}
                if not isinstance(body, dict):
                    body = {}

                filtered.append({
                    "name": name,
                    "query_params": query_params,
                    "body": body,
                })
            print("filtered", filtered)
            return {
                "endpoints": filtered,
                "reasoning": str(data.get("reasoning", "")).strip(),
            }

        except Exception as e:
            print("Exception when clarify user question", e)
            return default_plan

    async def _build_backend_context(self, question: str, token: str | None) -> dict:
        if not token:
            return {
                "auth_status": AuthStatus.MISSING_OR_INVALID.value,
                "profile": None,
                "deadlines": None,
                "calendar": None,
                "shared_documents": None,
                "documents": None,
                "errors": [],
            }

        buddy_service = get_buddy_service()
        plan = await self._plan_backend_endpoints(question=question, has_auth=True)
        print("plan", plan)
        selected_endpoints: list[dict] = plan.get("endpoints", [])
        endpoint_map = {
            ep["name"]: ep
            for ep in selected_endpoints
            if isinstance(ep, dict) and isinstance(ep.get("name"), str)
        }

        context: dict = {
            "auth_status": AuthStatus.OK.value,
            "profile": None,
            "deadlines": None,
            "calendar": None,
            "shared_documents": None,
            "documents": None,
            "errors": [],
        }

        if BackendEndpoint.USER_PROFILE.value in endpoint_map:
            try:
                context["profile"] = await buddy_service.get_user_profile(token=token)
            except BackendAPIError as exc:
                context["errors"].append(f"user_profile_error: {exc.status_code} {exc.detail}")

        if BackendEndpoint.SCHEDULE_DEADLINE_GET.value in endpoint_map:
            try:
                params = endpoint_map[BackendEndpoint.SCHEDULE_DEADLINE_GET.value].get("query_params", {})
                context["deadlines"] = await buddy_service.get_deadlines(
                    token=token,
                    page=params.get("page", 1),
                    limit=params.get("limit", 15),
                    sortType=params.get("sortType", "desc"),
                    sortBy=params.get("sortBy", "created_at"),
                    month=params.get("month"),
                    year=params.get("year"),
                )
            except BackendAPIError as exc:
                context["errors"].append(f"deadline_error: {exc.status_code} {exc.detail}")
        if BackendEndpoint.SCHEDULE_DEADLINE_CREATE.value in endpoint_map:
            try:
                params = endpoint_map[BackendEndpoint.SCHEDULE_DEADLINE_CREATE.value].get("body", {})
                context["deadline"] = await buddy_service.create_deadline(
                    token=token,
                    exerciseName=params.get("exerciseName"),
                    classCode=params.get("classCode"),
                    dueDate=params.get("dueDate"),
                )
            except BackendAPIError as exc:
                context["errors"].append(f"deadline_error: {exc.status_code} {exc.detail}")
        
        if BackendEndpoint.SCHEDULE_CALENDAR.value in endpoint_map:
            try:
                params = endpoint_map[BackendEndpoint.SCHEDULE_CALENDAR.value].get("query_params", {})
                context["calendar"] = await buddy_service.get_calendar(
                    token=token,
                    year=params.get("year"),
                    semester=params.get("semester"),
                )
            except BackendAPIError as exc:
                context["errors"].append(f"calendar_error: {exc.status_code} {exc.detail}")

        if BackendEndpoint.DOCUMENT_SHARED.value in endpoint_map:
            try:
                params = endpoint_map[BackendEndpoint.DOCUMENT_SHARED.value].get("query_params", {})
                context["shared_documents"] = await buddy_service.get_shared_documents(
                    token=token,
                    page=params.get("page", 1),
                    limit=params.get("limit", 15),
                    sortType=params.get("sortType", "desc"),
                    sortBy=params.get("sortBy", "createdAt"),
                    keyword=params.get("keyword", ""),
                )
            except BackendAPIError as exc:
                context["errors"].append(f"shared_documents_error: {exc.status_code} {exc.detail}")

        if BackendEndpoint.DOCUMENT_SEARCH.value in endpoint_map:
            try:
                params = endpoint_map[BackendEndpoint.DOCUMENT_SEARCH.value].get("query_params", {})
                context["documents"] = await buddy_service.search_documents(
                    token=token,
                    keyword=params.get("keyword", question),
                    page=params.get("page", 1),
                    limit=params.get("limit", 10),
                    sortType=params.get("sortType", "desc"),
                    sortBy=params.get("sortBy", "createdAt"),
                )
            except BackendAPIError as exc:
                context["errors"].append(f"document_error: {exc.status_code} {exc.detail}")
        
        if BackendEndpoint.DOCUMENT_DOWNLOAD.value in endpoint_map:
            try:
                params = endpoint_map[BackendEndpoint.DOCUMENT_DOWNLOAD.value].get("query_params", {})
                context["document"] = await buddy_service.download_document(
                    token=token,
                    fileId=params.get("fileId"),
                )
            except BackendAPIError as exc:
                context["errors"].append(f"document_error: {exc.status_code} {exc.detail}")        
        
        return context


    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Main chat handler.

        Every question goes through the same pipeline:
          1. Fetch user-specific backend context (skipped gracefully if no token).
          2. Retrieve academic context from LightRAG (hybrid mode).
          3. Call the LLM with both contexts and an improved system prompt.
          4. Fall back to a direct RAG answer if the final LLM call fails.
        """
        try:
            token = self._extract_token(request.authentication)

            backend_context, rag_context = await asyncio.gather(
                self._build_backend_context(request.question, token),
                query_context(question=request.question, mode="hybrid"),
            )

            llm_func = get_llm_func()
            user_prompt = CHAT_ANSWER_USER_TEMPLATE.format(
                question=request.question,
                backend_context=json.dumps(backend_context, ensure_ascii=False, indent=2),
                rag_context=rag_context or "No relevant academic context found.",
            )
            print("backend_context", backend_context)
            print("rag_context", rag_context)
            
            try:
                answer = await llm_func(
                    prompt=user_prompt,
                    system_prompt=CHAT_ANSWER_SYSTEM,
                    history=None,
                )
                print("answer", answer)
            except Exception as exc:
                print(f"[LLM final-answer error] {exc}")
                answer = await query(question=request.question, mode="hybrid")

            return ChatResponse(answer=answer)

        except ChatException:
            raise
        except Exception as exc:
            raise ChatException.from_definition(
                ChatErrorCode.PROCESSING_ERROR,
                message=f"{ChatErrorCode.PROCESSING_ERROR.message}: {exc}",
            )


    async def query(self, request: RagQueryRequest) -> RagQueryResponse:
        """Query LightRAG directly with a specific mode."""
        answer = await query(
            question=request.question,
            mode=request.mode,
            top_k=request.top_k,
            response_type=request.response_type,
            only_need_context=request.only_need_context,
        )
        return RagQueryResponse(answer=answer, mode=request.mode)

    async def query_context(self, question: str, mode: str = "hybrid", top_k: int = 60) -> str:
        """Query LightRAG but return only retrieved context, no LLM generation."""
        return await query_context(question=question, mode=mode, top_k=top_k)


    async def index(self, request: RagIndexRequest) -> RagIndexResponse:
        """Index documents into LightRAG. Returns doc IDs."""
        doc_ids = await index_documents(texts=request.documents)
        return RagIndexResponse(
            indexed_count=len(doc_ids),
            document_ids=doc_ids,
        )

    async def delete(self, doc_id: str) -> dict:
        """Delete a document from LightRAG."""
        return await delete_document(doc_id=doc_id)

    async def get_status(self, doc_id: str) -> dict:
        """Get processing status of a document."""
        return await get_document_status(doc_id=doc_id)


    async def seed_academic_data(self) -> RagSeedResponse:
        """Seed initial academic documents into LightRAG."""
        academic_docs = [
            "NT211 — Network Security: Covers network protocols, firewalls, IDS/IPS, VPN, and security auditing. Prerequisites: NT101. 3 credits.",
            "CS321 — Software Engineering: Software development lifecycle, agile, testing, CI/CD, DevOps practices. Prerequisites: CS201. 3 credits.",
            "NT548 — Cloud Architecture: AWS/GCP/Azure services, microservices, containers (Docker/K8s), IaC (Terraform). Prerequisites: NT211, CS321. 4 credits.",
            "NT212 — Network Infrastructure: Routing, switching, VLANs, OSPF, BGP, network design. Prerequisites: NT101. 3 credits.",
            "CS201 — Data Structures & Algorithms: Arrays, linked lists, trees, graphs, sorting, complexity analysis. Prerequisites: CS101. 3 credits.",
            "NT101 — Introduction to Networks: OSI model, TCP/IP, LAN/WAN, basic network setup. 3 credits.",
            "DevOps Track: NT101 → NT211 → NT212 → NT548. Key skills: Docker, Kubernetes, Terraform, CI/CD pipelines, monitoring.",
            "Data Engineering Track: CS101 → CS201 → CS301 → DE401. Key skills: SQL, Spark, Kafka, Airflow, cloud data warehouses.",
            "Data Science Track: CS101 → CS201 → CS301 → DS301. Key skills: Python, ML/DL, statistics, NLP, visualization.",
            "Course prerequisites: NT548 requires NT211 and CS321. CS321 requires CS201. CS201 requires CS101. DS301 requires CS301.",
            "Prerequisites chain: NT548 (Cloud) → NT211 (Security) → NT101. Also CS321 (DevOps) → CS201 → CS101.",
            "UIT grading policy: A (90-100), B (80-89), C (70-79), D (60-69), F (<60). Minimum passing grade: D (60).",
            "Maximum credits per semester: 21. Minimum enrollment: 12 credits. International students: minimum 15 credits.",
            "Credit transfer policy: Only courses with grade B+ or above from accredited institutions are considered for transfer.",
        ]
        doc_ids = await index_documents(texts=academic_docs)
        return RagSeedResponse(
            indexed_count=len(doc_ids),
            document_ids=doc_ids,
            sources=["academic_seed"],
        )


_rag_service: RagService | None = None


def get_rag_service() -> RagService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RagService()
    return _rag_service
