# Storage Layer

## 8 Storage Instances

When `LightRAG()` is initialized, it creates 8 storage instances:

```
LightRAG.__post_init__()
├── full_docs              → JsonKVStorage (namespace="full_docs")
├── text_chunks            → JsonKVStorage (namespace="text_chunks")
├── llm_response_cache     → JsonKVStorage (namespace="llm_cache")
├── doc_status             → JsonDocStatusStorage
├── chunks_vdb             → NanoVectorDBStorage
├── entities_vdb           → NanoVectorDBStorage
├── relationships_vdb      → NanoVectorDBStorage
└── chunk_entity_relation_graph → NetworkXStorage (or configured graph_storage)
```

## Each Storage Explained

### `full_docs` — JsonKVStorage
- **What:** Raw original document text (before chunking)
- **Key:** `compute_mdhash_id(doc_content)`
- **Value:** `{"content": str, "id": str}`
- **File:** `kv_store_full_docs.json`
- **Used by:** `adelete_by_doc_id()` to remove docs

### `text_chunks` — JsonKVStorage
- **What:** Token-split text chunks `{tokens, content, chunk_order_index}`
- **Key:** chunk hash ID
- **Value:** `{tokens, content, full_doc_id, chunk_order_index}`
- **File:** `kv_store_text_chunks.json`
- **Used by:** Entity extraction, query context building

### `chunks_vdb` — NanoVectorDBStorage
- **What:** Embeddings of text chunks (used in naive/mix modes)
- **Key:** chunk hash ID
- **Value:** `{content, vector, __created_at__}`
- **File:** `vdb_chunks.json`
- **Queried by:** `naive_query()`, `mix_kg_vector_query()`

### `entities_vdb` — NanoVectorDBStorage
- **What:** Embeddings of entity names + descriptions
- **Key:** entity hash ID
- **Value:** `{entity_name, description, source_id, vector, __created_at__}`
- **File:** `vdb_entities.json`
- **Queried by:** `local_query()` (low-level keywords)

### `relationships_vdb` — NanoVectorDBStorage
- **What:** Embeddings of relationship descriptions + keywords
- **Key:** relationship hash ID
- **Value:** `{source_entity, target_entity, description, keywords, vector, __created_at__}`
- **File:** `vdb_relationships.json`
- **Queried by:** `global_query()` (high-level keywords)

### `chunk_entity_relation_graph` — NetworkXStorage
- **What:** Entity nodes + relationship edges (the knowledge graph)
- **Nodes:** `{entity_name, entity_type, description, source_id, level}`
- **Edges:** `{source, target, description, weight, keywords}`
- **File:** `graph_{namespace}.graphml`
- **Queried by:** All non-naive query modes (graph traversal)
- **Key methods:** `get_node()`, `get_node_edges()`, `node_degree()`, `edge_degree()`

### `llm_response_cache` — JsonKVStorage
- **What:** Cached LLM responses
- **Key:** `compute_args_hash(query_args)`
- **Value:** `{prompt, response, creation_time, quantized_prompt_embedding}`
- **File:** `kv_store_llm_response_cache.json`
- **Used by:** `handle_cache()`, `save_to_cache()`

### `doc_status` — JsonDocStatusStorage
- **What:** Document processing lifecycle status
- **Key:** `doc_id`
- **Value:** `{content_summary, content_length, status, chunks_count, timestamps, error, metadata}`
- **File:** `kv_store_doc_status.json`
- **Statuses:** `PENDING → PROCESSING → PROCESSED` or `FAILED`

## Storage Operations at Indexing Time

```
ainsert(text)
  │
  ▼
full_docs.upsert({doc_id: {content: text, id: doc_id}})
  │
  ▼
chunking_by_token_size(text)
  │
  ▼
For each chunk:
  │
  ├─ text_chunks.upsert(chunk_data)
  ├─ chunks_vdb.upsert(chunk + embedding)
  ├─ extract_entities()
  │   ├─ entities_vdb.upsert(entity + embedding)
  │   ├─ relationships_vdb.upsert(rel + embedding)
  │   ├─ chunk_entity_relation_graph.upsert_node()
  │   └─ chunk_entity_relation_graph.upsert_edge()
  │   │
  │   └─ doc_status.upsert() (PROCESSING → PROCESSED)
  │
  ▼
_insert_done()
  │
  ▼
All storages call index_done_callback()
  → Persist to JSON / GraphML files
```

## Storage Operations at Query Time

```
aquery(query, mode)
  │
  ├─ Cache check (llm_response_cache)
  │     └─ Hit → return cached response
  │
  ▼ [cache miss]
  │
  ├─ naive mode:
  │     └─ chunks_vdb.query() → text_chunks.get_by_ids()
  │
  ├─ local mode:
  │     └─ entities_vdb.query() → graph traversal → text_chunks lookup
  │
  ├─ global mode:
  │     └─ relationships_vdb.query() → graph traversal → text_chunks lookup
  │
  ├─ hybrid mode:
  │     └─ local_query() + global_query() → combine_contexts()
  │
  └─ mix mode:
        └─ KG search + chunks_vdb.query() (parallel)
  │
  ▼
save_to_cache()
  │
  ▼
Return response
```

## Swapping Storage Backends

```python
# Neo4j for the graph
rag = LightRAG(
    ...
    graph_storage="Neo4JStorage",  # env: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
)

# PostgreSQL full stack
rag = LightRAG(
    ...
    kv_storage="PGKVStorage",
    vector_storage="PGVectorStorage",
    graph_storage="PGGraphStorage",
)

# TiDB cloud
rag = LightRAG(
    ...
    kv_storage="TiDBKVStorage",
    vector_storage="TiDBVectorDBStorage",
    graph_storage="TiDBGraphStorage",
)
```

## Document Deletion with `GRAPH_FIELD_SEP`

When an entity appears in multiple documents, its `source_id` field contains all doc IDs joined by `"<SEP>"`:

```
source_id = "doc_abc<SEP>doc_def<SEP>doc_ghi"
```

When deleting `doc_abc`:
1. Split `source_id` by `"<SEP>"`
2. Remove `doc_abc` from the list
3. If list is empty → delete the entity node
4. If list still has items → update `source_id` with remaining IDs

This ensures entities shared across documents are preserved.
