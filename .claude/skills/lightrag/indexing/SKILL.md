---
name: lightrag-indexing
description: "Use when the user asks how documents are indexed, how entity extraction works, or what happens during the insert pipeline. Examples: 'How does document indexing work?', 'What is the gleaning loop?', 'How are entities extracted?'"
---

# LightRAG — Indexing Pipeline

## Full Indexing Flow

```
DOCUMENT INPUT
     │
     ▼
┌─────────────────────────────────────────────────┐
│  LightRAG.ainsert(text)                        │
│  1. Generate doc IDs + PENDING status          │
│  2. Filter already-processed docs (idempotent) │
│  3. Batch process each document                │
└─────────────────────────────────────────────────┘
     │
     ▼
chunking_by_token_size()
     │
     ▼
extract_entities()
     │
     ▼
STORAGE UPSERT
├── NanoVectorDB (chunks_vdb, entities_vdb, relationships_vdb)
├── JsonKVStorage (full_docs, text_chunks)
└── NetworkXStorage (graph)
```

## Step 1 — Chunking

**`chunking_by_token_size(content)`**

```
Raw text → tiktoken encode (gpt-4o model)
→ Sliding window: max_token_size=1024, overlap=100 tokens
→ Output: [{"tokens": N, "content": str, "chunk_order_index": i}, ...]
```

**Why tiktoken?** LightRAG counts tokens (not characters) because LLM APIs bill/use context by token. Character-based chunking would produce chunks of wildly different token counts.

**Config:**
- `chunk_token_size` (default 1024) — max tokens per chunk
- `chunk_overlap_token_size` (default 100) — overlap between consecutive chunks
- `tiktoken_model_name` (default "gpt-4o-mini") — tokenizer model

## Step 2 — Entity Extraction

**`extract_entities(chunks, ...)`** — called once per chunk

```
For each chunk:
  1. Build entity_extraction prompt (with few-shot examples)
  2. LLM extraction → raw output
  3. Parse via regex → nodes (entities) + edges (relationships)
  4. Loop: "MANY entities were missed. Add them below:"
     → until max_gleaning or LLM says "NO"
  5. _handle_entity_relation_summary() → LLM summarization of descriptions
  6. _merge_nodes_then_upsert() → deduplicate + upsert to KV storage
  7. _merge_edges_then_upsert() → deduplicate + upsert to KV storage
  8. Upsert entity vectors → entities_vdb
  9. Upsert relationship vectors → relationships_vdb
  10. Upsert nodes/edges → NetworkXStorage graph
```

### Entity Extraction Output Format

The LLM is prompted to output in this format:
```
##{entity_name}<|>{entity_type}<|>{entity_description}##
##{source_entity}<|>{target_entity}<|>{relationship_description}<|>{strength}<|>{keywords}##
```

**Default entity types:** `["organization", "person", "geo", "event", "category"]`
**Delimiters:** `TUPLE_DELIMITER = "<|>"`, `RECORD_DELIMITER = "##"`

### The Gleaning Loop

After the first LLM extraction, LightRAG loops to catch missed entities:

1. `entiti_continue_extraction` prompt: "MANY entities were missed. Add them below:"
2. `entiti_if_loop_extraction` prompt: "Is there still entities to add? YES | NO"
3. Loop `max_gleaning` times (default: 1) or until LLM says NO

**Why?** LLM extraction is imperfect. The gleaning loop catches entities that were missed in the first pass, especially from long text chunks.

### Entity Summary

**`_handle_entity_relation_summary()`** calls the LLM with `summarize_entity_descriptions` prompt to merge multiple descriptions of the same entity into one clean summary.

## Step 3 — Storage Upsert

### What Gets Stored

| Storage | What Gets Stored |
|---|---|
| `full_docs` | Raw document text (JsonKVStorage) |
| `text_chunks` | Token-split chunks (JsonKVStorage) |
| `chunks_vdb` | Chunk text + embedding (NanoVectorDB) |
| `entities_vdb` | Entity name + description + embedding (NanoVectorDB) |
| `relationships_vdb` | Relationship description + keywords + embedding (NanoVectorDB) |
| `chunk_entity_relation_graph` | Entity nodes + relationship edges (NetworkX) |

### Embedding Batching

`NanoVectorDBStorage.upsert()` batches embedding generation:
- Splits content into batches of `embedding_batch_num` (default 32)
- Generates embeddings concurrently
- Upserts to NanoVectorDB with progress bar (tqdm)

## Document Status Lifecycle

```
ainsert() → set status PENDING
  │
  ▼
Process chunking → set status PROCESSING + chunks_count
  │
  ▼
extract_entities() → success → set status PROCESSED
                └── exception → set status FAILED
```

Query: `get_document_status()` → `DocProcessingStatus` dataclass.

## Idempotency

`ainsert()` filters out already-processed docs by checking `compute_mdhash_id()` against existing IDs. Safe to call multiple times with the same document.

## Deleting a Document

**`adelete_by_doc_id(doc_id)`** removes all data associated with a document:
1. Removes from `full_docs`, `text_chunks`, `chunks_vdb`
2. For entities: checks `GRAPH_FIELD_SEP` — if this doc was the only source, delete the entity node; otherwise only remove this doc's source ID
3. Same logic for relationships
4. Updates graph and all KV stores

## Config Parameters

| Parameter | Default | Purpose |
|---|---|---|
| `insert_batch_size` | `10` | Docs per batch |
| `entity_extract_max_gleaning` | `1` | Gleaning loop iterations |
| `entity_summary_to_max_tokens` | `500` | Max tokens for entity summary LLM call |
| `embedding_batch_num` | `32` | Embedding batch size |
| `cosine_better_than_threshold` | `0.2` | Min similarity for vector results |
