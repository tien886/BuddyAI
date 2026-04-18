---
name: lightrag-troubleshooting
description: "Use when the user is debugging a LightRAG issue, entity extraction problem, or unexpected query results. Examples: 'Why is extraction missing entities?', 'Query returns nothing', 'LLM calls failing', 'Slow indexing'"
---

# LightRAG — Troubleshooting

## Entity Extraction Issues

### ❌ Entities missing from extraction

**Symptoms:** Document indexed but fewer entities than expected.

**Likely causes:**
1. **Gleaning loop too short** — default is `max_gleaning=1`. Increase in constructor:
   ```python
   rag = LightRAG(
       ...
       entity_extract_max_gleaning=3,  # More loops
   )
   ```
2. **Entity type not in default list** — default types are `["organization", "person", "geo", "event", "category"]`. Add custom types:
   ```python
   rag = LightRAG(
       ...
       entity_types=["course", "skill", "tool", "certification"],
   )
   ```
3. **LLM output parsing failed** — check if the LLM is outputting in the right format. Add debug logging:
   ```python
   from lightrag.utils import set_logger
   set_logger("DEBUG")
   ```

### ❌ Duplicate entities

**Cause:** Same entity extracted from multiple chunks. LightRAG deduplicates via `_merge_nodes_then_upsert()`. If duplicates appear, check that `compute_mdhash_id()` is producing stable IDs. No action needed — this is expected behavior.

### ❌ Entity descriptions are empty or wrong

**Fix:** `_handle_entity_relation_summary()` summarizes descriptions via LLM. Increase token budget:
```python
entity_summary_to_max_tokens=800  # Default is 500
```

## Query Issues

### ❌ Query returns no results / empty context

**Likely causes:**
1. **No documents indexed** — call `ainsert()` before querying
2. **Wrong query mode** — try `mode="naive"` first (uses raw chunks, simpler)
3. **Embedding dimension mismatch** — embedding dim must match what was used at indexing time. Verify with `get_embedding_dim()`
4. **Query too specific** — try broader keywords or increase `top_k`

**Debug approach:**
```python
# Test with naive mode first (simplest path)
result = await rag.aquery("your query", param=QueryParam(mode="naive"))

# If naive works but hybrid doesn't, the issue is in KG search
result = await rag.aquery("your query", param=QueryParam(mode="hybrid", only_need_context=True))
# only_need_context=True returns retrieved context without LLM call
```

### ❌ Wrong/irrelevant results

**Fixes:**
1. Increase `top_k` to retrieve more candidates:
   ```python
   param=QueryParam(mode="hybrid", top_k=100)
   ```
2. Lower cosine threshold for broader results:
   ```python
   cosine_better_than_threshold=0.1  # Default is 0.2
   ```
3. Try different mode — `hybrid` combines local + global. If results are too broad, try `local`. If too narrow, try `global`.

### ❌ Slow queries

**Likely cause:** LLM is being called for every query. Enable response caching:
```python
rag = LightRAG(
    ...
    enable_llm_cache=True,  # Default is True, verify it's not disabled
)
```

Cache location: `kv_store_llm_response_cache.json`.

## LLM & Embedding Issues

### ❌ LLM API errors

**Check retry logic:** All LLM calls use `tenacity` with exponential backoff (3 attempts, 4-10s wait). If persistent, check:
1. API key is correct
2. Base URL is correct (e.g., Claude needs `https://api.Claude.com/v1`)
3. Rate limits — decrease `llm_model_max_async`:
   ```python
   llm_model_max_async=8  # Default is 16
   ```

### ❌ Embedding dimension mismatch

**Symptom:** `ValueError` on `NanoVectorDBStorage.query()`

**Fix:** Always detect dimension dynamically:
```python
test = await embed_func(["test"])
dim = test.shape[1]  # Get actual dimension
embedding_func=EmbeddingFunc(embedding_dim=dim, ...)
```

## Storage Issues

### ❌ Data not persisting after restart

**Cause:** `_insert_done()` may not have been called. Ensure:
1. Indexing completes fully (status = PROCESSED)
2. `index_done_callback()` runs on all storages

### ❌ Neo4j connection fails

**Check env vars:**
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```
Verify Neo4j is running: `bolt://localhost:7687` should be reachable.

## Indexing Performance

### ❌ Slow indexing for large documents

**Optimizations:**
1. **Increase embedding batch size:**
   ```python
   embedding_batch_num=64  # Default is 32
   ```
2. **Reduce concurrent LLM calls:**
   ```python
   llm_model_max_async=32  # Default is 16
   ```
3. **Lower chunk overlap:**
   ```python
   chunk_overlap_token_size=50  # Default is 100
   ```

### ❌ Memory issues with large documents

**Fix:** Process in smaller batches:
```python
rag = LightRAG(
    ...
    insert_batch_size=5,  # Default is 10
)
```

## Debug Logging

Enable full debug logging to see actual LLM prompts and responses:

```python
from lightrag.utils import set_logger
set_logger("DEBUG")  # or "INFO" for less verbosity
```

This logs:
- LLM prompts being sent
- Parsed entity/relationship outputs
- Storage upsert operations
- Cache hits/misses
