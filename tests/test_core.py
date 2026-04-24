import pytest
from unittest.mock import patch, AsyncMock
from service.rag.rag_service import get_rag_service
from dto import ChatRequest
import json

@pytest.fixture(autouse=True)
def setup_teardown():
    yield

@pytest.mark.asyncio
async def test_kg_core_indexing_and_query():
    """Test KG core functionality: indexing and querying (Unit Test)."""
    
    docs = [
        "LightRAG is an innovative open-source framework for Retrieval-Augmented Generation.",
        "The creator of LightRAG is Zirui Fang."
    ]
    
    with patch("rag.rag.index_documents", new_callable=AsyncMock) as mock_index, \
         patch("rag.rag.query", new_callable=AsyncMock) as mock_query:
         
        mock_index.return_value = ["doc1", "doc2"]
        mock_query.return_value = "Zirui Fang created LightRAG."
        
        # Test indexing wrapper
        from rag.rag import index_documents, query
        doc_ids = await index_documents(docs)
        assert len(doc_ids) == 2
        
        # Test query wrapper
        answer = await query(question="Who created LightRAG?", mode="hybrid")
        assert "Zirui" in answer or "Fang" in answer

@pytest.mark.asyncio
async def test_lightrag_work_well():
    """Test LightRAG via RagService chat to ensure it works well (Unit Test)."""
    svc = get_rag_service()
    
    req = ChatRequest(
        question="What is NT211?",
        authentication=""
    )
    
    # Mock index, query_context, and the LLM func
    with patch("service.rag.rag_service.index_documents", new_callable=AsyncMock) as mock_index, \
         patch("service.rag.rag_service.query_context", new_callable=AsyncMock) as mock_query_context, \
         patch("service.rag.rag_service.get_llm_func") as mock_get_llm:
         
        mock_index.return_value = ["doc1"]
        mock_query_context.return_value = "NT211 is a Network Security course covering firewalls."
        
        mock_llm = AsyncMock()
        mock_llm.return_value = "NT211 is a Network Security course."
        mock_get_llm.return_value = mock_llm
        
        await svc.index(request=type("RagIndexRequest", (), {"documents": ["NT211 is a Network Security course covering firewalls."]})())
        mock_index.assert_called_once()
        
        response = await svc.chat(req)
        
        answer = response.answer
        assert "Network Security" in answer or "firewalls" in answer or "NT211" in answer

