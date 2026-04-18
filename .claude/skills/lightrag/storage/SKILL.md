---
name: lightrag-storage
description: "Use when the user asks about storage backends, how to swap storage (e.g. NetworkX → Neo4j), or how data is persisted. Examples: 'How do I use Neo4j?', 'Where is data stored?', 'Swap vector store to Milvus'"
---

# LightRAG — Storage Layer

## Architecture

All storage backends implement abstract interfaces from `lightrag/base.py`. LightRAG is designed so swapping a storage backend requires only changing the constructor parameter.

```
lightrag/base.py
├── BaseVectorStorage     ← implemented by: NanoVectorDBStorage, ChromaVectorDBStorage, MilvusVectorDBStorge, PGVectorStorage, TiDBVectorDBStorage, OracleVectorDBStorage
├── BaseKVStorage[T]     ← implemented by: JsonKVStorage, MongoKVStorage, PGKVStorage, TiDBKVStorage, OracleKVStorage
├── BaseGraphStorage     ← implemented by: NetworkXStorage, Neo4JStorage, PGGraphStorage, TiDBGraphStorage, OracleGraphStorage, AGEStorage, GremlinStorage
└── DocStatusStorage     ← implemented by: JsonDocStatusStorage
```

## Default Storage Setup

| Instance | Class | File | What It Stores |
|---|---|---|---|
| `full_docs` | `JsonKVStorage` | `kv_store_full_docs.json` | Raw original documents |
| `text_chunks` | `JsonKVStorage` | `kv_store_text_chunks.json` | Token-split chunks |
| `chunks_vdb` | `NanoVectorDBStorage` | `vdb_chunks.json` | Chunk embeddings |
| `entities_vdb` | `NanoVectorDBStorage` | `vdb_entities.json` | Entity embeddings |
| `relationships_vdb` | `NanoVectorDBStorage` | `vdb_relationships.json` | Relationship embeddings |
| `llm_response_cache` | `JsonKVStorage` | `kv_store_llm_response_cache.json` | Cached LLM responses |
| `doc_status` | `JsonDocStatusStorage` | `kv_store_doc_status.json` | Document processing status |
| `chunk_entity_relation_graph` | `NetworkXStorage` | `graph_{namespace}.graphml` | Entity nodes + relationship edges |

## Available Storage Backends

### Vector Storage

| Backend | Class | Config |
|---|---|---|
| **NanoVectorDB** (default) | `NanoVectorDBStorage` | Via `working_dir` |
| ChromaDB | `ChromaVectorDBStorage` | `global_config` |
| Milvus | `MilvusVectorDBStorge` | `global_config` |
| PostgreSQL + pgvector | `PGVectorStorage` | `global_config` |
| TiDB Vector | `TiDBVectorDBStorage` | `global_config` |
| Oracle AI Vector | `OracleVectorDBStorage` | `global_config` |

### Key-Value Storage

| Backend | Class | Config |
|---|---|---|
| **JSON file** (default) | `JsonKVStorage` | Via `working_dir` |
| MongoDB | `MongoKVStorage` | `global_config` |
| PostgreSQL | `PGKVStorage` | `global_config` |
| TiDB | `TiDBKVStorage` | `global_config` |
| Oracle | `OracleKVStorage` | `global_config` |

### Graph Storage

| Backend | Class | Config |
|---|---|---|
| **NetworkX** (default) | `NetworkXStorage` | Via `working_dir` |
| Neo4j | `Neo4JStorage` | `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` env vars |
| PostgreSQL + Apache AGE | `PGGraphStorage` | `global_config` |
| TiDB Graph | `TiDBGraphStorage` | `global_config` |
| Oracle Property Graph | `OracleGraphStorage` | `global_config` |
| Apache AGE | `AGEStorage` | `global_config` |
| Gremlin (JanusGraph/OrientDB) | `GremlinStorage` | `global_config` |

### Doc Status Storage

| Backend | Class | Config |
|---|---|---|
| **JSON file** (default) | `JsonDocStatusStorage` | Via `working_dir` |

## Swapping Storage Backends

### Example: Swap NetworkX → Neo4j

```python
import os
from lightrag import LightRAG

rag = LightRAG(
    working_dir="./working",
    llm_model_func=my_llm_func,
    embedding_func=my_embedding_func,
    graph_storage="Neo4JStorage",  # ← Change this
)
```

**Required env vars for Neo4j:**
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

### Example: Swap to PostgreSQL + pgvector (Full Stack)

```python
rag = LightRAG(
    working_dir="./working",
    llm_model_func=my_llm_func,
    embedding_func=my_embedding_func,
    kv_storage="PGKVStorage",
    vector_storage="PGVectorStorage",
    graph_storage="PGGraphStorage",
    doc_status_storage="PGDocStatusStorage",  # if available
)
```

### Example: Swap to TiDB (Cloud)

```python
rag = LightRAG(
    working_dir="./working",
    llm_model_func=my_llm_func,
    embedding_func=my_embedding_func,
    kv_storage="TiDBKVStorage",
    vector_storage="TiDBVectorDBStorage",
    graph_storage="TiDBGraphStorage",
)
```

## Lazy Imports

Heavy graph DB drivers (Neo4j, Oracle, etc.) use `lazy_external_import()` — they're only loaded when you actually select them in the constructor. This keeps the base import fast.

## Storage Lifecycle

1. **At startup:** Each storage may call `load_nx_graph()` to reload persisted data (e.g., NetworkX reloads from `.graphml`)
2. **During indexing:** Data upserts to all active storages
3. **After indexing:** `_insert_done()` → calls `index_done_callback()` on each storage → persists to disk
4. **At shutdown:** All data is persisted (JSON files, GraphML, etc.)

## Document Status (`DocStatus`)

Tracks document lifecycle:

```
PENDING → PROCESSING → PROCESSED
                        └── FAILED (on exception)
```

Query: `doc_status.get_status_counts()` → returns counts of each status.

## Caching

`llm_response_cache` (`JsonKVStorage`) stores LLM responses keyed by `compute_args_hash()`. Two tiers:
1. **Exact match** — hash of (mode + query + history) → instant hit
2. **Embedding similarity** — quantized query embedding → cosine similarity check → optional LLM verification

## Key Design: `GRAPH_FIELD_SEP = "<SEP>"`

When the same entity appears in multiple documents, LightRAG stores all source IDs joined by `"<SEP>"`. This allows `adelete_by_doc_id()` to cleanly remove a document's entities without affecting entities shared with other documents.
