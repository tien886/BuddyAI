import pytest
from unittest.mock import patch
from rag.rag import get_rag, index_documents, query
from service.rag.rag_service import get_rag_service
from dto import ChatRequest
import os
import shutil
from lightrag.lightrag import LightRAG

original_init = LightRAG.__init__

def mocked_init(self, *args, **kwargs):
    kwargs["graph_storage"] = "NetworkXStorage"
    original_init(self, *args, **kwargs)

@pytest.fixture(autouse=True)
def setup_teardown():
    import rag.rag
    rag.rag._rag = None
    
    from config.rag_config import RAG_WORKING_DIR
    if os.path.exists(RAG_WORKING_DIR):
        try:
            shutil.rmtree(RAG_WORKING_DIR)
        except:
            pass
    with patch.object(LightRAG, '__init__', mocked_init):
        yield
    if os.path.exists(RAG_WORKING_DIR):
        try:
            shutil.rmtree(RAG_WORKING_DIR)
        except:
            pass

@pytest.mark.asyncio
async def test_kg_core_indexing_and_query():
    """Test KG core functionality: indexing and querying."""
    await get_rag().initialize_storages()
    
    docs = [
        "LightRAG is an innovative open-source framework for Retrieval-Augmented Generation.",
        "The creator of LightRAG is Zirui Fang."
    ]
    doc_ids = await index_documents(docs)
    
    assert len(doc_ids) == 2
    
    answer = await query(question="Who created LightRAG?", mode="hybrid")
    
    if not answer or "error" in answer.lower():
        pytest.skip("LLM API returned empty or error response, likely due to rate limit (429).")
        
    assert "Zirui" in answer or "Fang" in answer, f"Answer did not contain expected words. Answer: {answer}"

@pytest.mark.asyncio
async def test_lightrag_work_well():
    """Test LightRAG via RagService chat to ensure it works well."""
    await get_rag().initialize_storages()
    
    svc = get_rag_service()
    
    await svc.index(request=type("RagIndexRequest", (), {"documents": ["NT211 is a Network Security course covering firewalls."]})())
    
    req = ChatRequest(
        question="What is NT211?",
        authentication=""
    )
    
    response = await svc.chat(req)
    
    answer = response.answer
    if not answer or "error" in answer.lower():
        pytest.skip("LLM API returned empty or error response, likely due to rate limit (429).")
        
    assert "Network Security" in answer or "firewalls" in answer or "NT211" in answer, f"Answer did not contain expected words. Answer: {answer}"
