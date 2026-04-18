---
name: lightrag-architecture
description: "Use when the user asks how LightRAG works, wants to understand the project structure, or needs a high-level overview. Examples: 'How does LightRAG work?', 'Show me the architecture', 'What are the main components?'"
---

# LightRAG — Architecture

## What Is LightRAG?

LightRAG is a **Retrieval-Augmented Generation** framework that combines:
- **Vector search** — semantic similarity on text chunks
- **Knowledge graph** — entity-relationship extraction and graph traversal
- **LLM reasoning** — generation from retrieved context

It indexes documents → extracts entities/relationships → builds a searchable KG → answers queries with context from both vector and graph search.

## Project Structure

```
LightRAG/
├── server.py                  # FastAPI entry point (port 20000)
├── controller/
│   └── BuddyService.py      # Request handling
├── dto/
│   └── ChatRequest.py         # Pydantic request models
├── lightrag/                  # Core library (pip package: lightrag-hku)
│   ├── lightrag.py            # Main orchestrator (LightRAG class)
│   ├── operate.py             # Core ops: chunking, entity extract, queries
│   ├── storage.py             # Storage backends (JsonKV, NanoVectorDB, NetworkX)
│   ├── base.py                # Abstract interfaces + data schemas
│   ├── llm.py                 # LLM + embedding function wrappers
│   ├── prompt.py              # All LLM prompt templates
│   └── utils.py               # Utilities (hashing, tokenization, caching)
└── .claude/
    ├── skills/lightrag/       # This skill directory
    └── context-memory/        # Agent brain docs
```

## Key Classes

### `LightRAG` (`lightrag/lightrag.py`)
The **orchestrator**. Wires together all storage, LLM, and operations.
- `ainsert(text)` → index documents
- `aquery(query, param)` → query with mode routing
- `adelete_by_doc_id(id)` → remove document

### `operate.py` — Operations Engine
| Function | Purpose |
|---|---|
| `chunking_by_token_size()` | Token-aware text splitting (tiktoken, sliding window) |
| `extract_entities()` | LLM entity/relationship extraction + gleaning loop |
| `naive_query()` | Pure vector search on text chunks |
| `kg_query()` | KG search (local/global mode) |
| `mix_kg_vector_query()` | Parallel KG + vector search (mix mode) |

### `storage.py` — Storage Backends
| Class | Type | Persisted To |
|---|---|---|
| `JsonKVStorage` | KV | `kv_store_{namespace}.json` |
| `NanoVectorDBStorage` | Vector | `vdb_{namespace}.json` |
| `NetworkXStorage` | Graph | `graph_{namespace}.graphml` |
| `JsonDocStatusStorage` | Doc Status | `kv_store_doc_status.json` |

### `base.py` — Abstract Interfaces
| Class | Key Methods |
|---|---|
| `BaseVectorStorage` | `upsert(data)`, `query(query, top_k)` |
| `BaseKVStorage` | `get_by_id()`, `upsert()`, `filter_keys()` |
| `BaseGraphStorage` | `upsert_node()`, `upsert_edge()`, `get_node()`, `get_node_edges()` |

## 5 Storage Instances Created at Startup

```
LightRAG()
├── full_docs              → JsonKVStorage (namespace=full_docs)
├── text_chunks           → JsonKVStorage (namespace=text_chunks)
├── llm_response_cache    → JsonKVStorage (namespace=llm_cache)
├── doc_status            → JsonDocStatusStorage
├── chunks_vdb            → NanoVectorDBStorage (chunk vectors)
├── entities_vdb          → NanoVectorDBStorage (entity vectors)
├── relationships_vdb     → NanoVectorDBStorage (relationship vectors)
└── chunk_entity_relation_graph → NetworkXStorage / Neo4JStorage
```

## Config Parameters

| Parameter | Default | Purpose |
|---|---|---|
| `working_dir` | `"working"` | Base dir for all storage files |
| `chunk_token_size` | `1024` | Max tokens per chunk |
| `chunk_overlap_token_size` | `100` | Token overlap |
| `llm_model_max_async` | `16` | Max concurrent LLM calls |
| `llm_model_max_token_size` | `32768` | LLM context window |
| `embedding_func` | `EmbeddingFunc` | Embedding function |
| `kv_storage` | `"JsonKVStorage"` | KV backend |
| `vector_storage` | `"NanoVectorDBStorage"` | Vector backend |
| `graph_storage` | `"NetworkXStorage"` | Graph backend |

## LLM & Embedding Backends

**LLM** (via `llm.py`): OpenAI, Claude (OpenAI-compatible), Ollama, Azure, HuggingFace, LoLLMs, LMDeploy, Zhipu, NVIDIA NIM, etc.

**Embedding**: OpenAI, Ollama, HuggingFace, SiliconCloud, Jina, Azure, NVIDIA NIM, Zhipu, etc.

**Default in agent** (Claude-Test): LLM=Claude-reasoner via SiliconCloud-compatible API, Embedding=BAAI/bge-m3.
