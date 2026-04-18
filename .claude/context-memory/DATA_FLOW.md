# Data Flow

## End-to-End Flow Summary

### Indexing Flow (Document → Knowledge Graph)

```
DOCUMENT INPUT (PDF/TXT/DOCX/MD)
    │
    ▼ textract.process()
RAW TEXT
    │
    ▼ compute_mdhash_id(doc_content)
GENERATE DOC ID
    │
    ▼ doc_status.set(PENDING)
TRACK DOCUMENT STATUS
    │
    ▼ chunking_by_token_size()  [operate.py]
TOKEN-SPLIT INTO CHUNKS
    │
    │ chunks: [{tokens, content, chunk_order_index}, ...]
    │
    ├─────────────────────────────────────────────┐
    ▼                                             ▼
upsert text_chunks                          extract_entities()  [operate.py]
upsert chunks_vdb (vector)                  ┌─────────────────────────────┐
                                          │ For each chunk:              │
                                          │ 1. entity_extraction prompt  │
                                          │ 2. LLM → raw output          │
                                          │ 3. Parse regex → nodes+edges │
                                          │ 4. Gleaning loop (max 1x)   │
                                          │ 5. summarize descriptions    │
                                          │ 6. _merge_nodes_then_upsert()│
                                          │ 7. _merge_edges_then_upsert()│
                                          └─────────────────────────────┘
                                                │
                                          ┌─────┴──────┬──────────────┐
                                          ▼            ▼              ▼
                                    upsert to    upsert to      upsert to
                                    entities_vdb  relationships_vdb  NetworkX
                                    (NanoVecDB)    (NanoVecDB)    (graph)
                                          │            │              │
                                          └────────────┴──────────────┘
                                                    │
                                          doc_status.set(PROCESSED)
                                                    │
                                                    ▼
                                          _insert_done()
                                                    │
                                                    ▼
                                          All storages: index_done_callback()
                                                    │
                                                    ▼
                                          PERSISTED TO DISK
                                          ├── kv_store_*.json
                                          ├── vdb_*.json
                                          └── graph_*.graphml
```

### Query Flow (Question → Answer)

```
USER QUERY: "What should I study for a DevOps career?"
    │
    ▼
aquery(query, param=QueryParam(mode="hybrid"))
    │
    ├─ Cache check (llm_response_cache)
    │     └─ compute_args_hash() → hit? → return cached
    │
    ▼ [cache miss]
    │
    ▼ keywords_extraction()  [prompt.py]
    │
    │ Returns: {high_level_kw: [...], low_level_kw: [...]}
    │
    ├──────────────────────────────┐
    ▼                              ▼
local_query()                  global_query()
    │                              │
    │ ll_keywords                  │ hl_keywords
    ▼                              ▼
entities_vdb.query()     relationships_vdb.query()
    │                              │
    ▼                              ▼
get_node() + node_degree()    get_edge() + edge_degree()
    │                              │
    ▼                              ▼
1-hop neighbor expansion       endpoint entities
    │                              │
    ▼                              ▼
text_chunks lookup             text_chunks linked to edges
    │                              │
    ▼                              ▼
truncate (≤4000 tokens)        truncate (≤4000 tokens)
    │                              │
    └────────────┬─────────────────┘
                 ▼
         process_combine_contexts()
         (deduplicate CSV rows + merge)
                 │
                 ▼
         mix_rag_response prompt
         ({kg_context: combined local+global})
                 │
                 ▼
         LLM (Claude/SiliconCloud)
                 │
                 ▼
         save_to_cache()
                 │
                 ▼
         FINAL ANSWER
```

## Context Builder (Before LLM Call)

Before calling the LLM, BuddyAI merges data from multiple sources:

```
Backend Data (user-specific)   LightRAG KG Data (knowledge)
├── schedules                  ├── entities
├── deadlines                  ├── relationships
├── enrolled courses           └── topics
└── student context
         │
         ▼
  Context Builder
  ├── merge + deduplicate
  ├── resolve conflicts
  ├── label uncertainty (outdated info)
  └── format as structured input
         │
         ▼
  LLM System Prompt
```

## BuddyAI Decision Gate → LightRAG

```
User Question
    │
    ▼
Is it in-domain?
    │
    ├─ NO ("What is the weather?")
    │     └─ skip_all → direct response
    │
    └─ YES ↓
    │
    ▼
Is it Fast?
    │
    ├─ YES ("hello", "summarize this")
    │     └─ direct response (no LightRAG)
    │
    └─ NO ↓
    │
    ▼
Is it Lookup?
    │
    ├─ YES ("what is NT211?", "deadlines today")
    │     └─ LightRAG (naive/local mode) → response
    │         (no n8n, no heavy pipeline)
    │
    └─ NO ↓
    │
    ▼
Thinking Question
    │
    ▼
TRIGGER LIGHTRAG + n8n + LLM PIPELINE
    │
    ├─ Validate Access
    ├─ Backend (user data)
    ├─ LightRAG (knowledge graph) → context
    ├─ Context Builder (merge + deduplicate)
    ├─ n8n Workflow (orchestration)
    ├─ LLM (Gemini) → explanation
    └─ Response (grounded + uncertainty labeled)
```

## Key Design Principles

1. **Never over-trigger n8n** — n8n runs only for `thinking` questions
2. **Separate concerns** — Decision Gate routes, Backend provides user data, LightRAG provides knowledge, LLM explains
3. **Prefer cheap paths first** — fast → lookup → thinking (most expensive)
4. **Grounded answers** — all LLM responses are grounded in retrieved data, never hallucinated facts
5. **Uncertainty labeling** — if info may be outdated or uncertain, it's labeled in the response
