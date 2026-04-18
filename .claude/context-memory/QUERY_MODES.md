# Query Modes

## Quick Reference

| Mode | What It Searches | How It Searches | Best For |
|---|---|---|---|
| `naive` | Text chunks (`chunks_vdb`) | Vector similarity only | Simple Q&A |
| `local` | Entities (`entities_vdb`) | Entity → 1-hop neighbors → text | "Tell me about [entity]" |
| `global` | Relationships (`relationships_vdb`) | Relationship → connected entities | "What's connected to [topic]?" |
| `hybrid` | Entities + Relationships | local + global, merged | General exploratory (DEFAULT) |
| `mix` | KG + Text Chunks (parallel) | KG search + vector search | Maximum recall |

## Mode Flow Diagrams

### naive — Pure Vector Search

```
User Query
    │
    ▼
chunks_vdb.query(query_embedding, top_k)
    │
    ▼
text_chunks.get_by_ids(matching_ids)
    │
    ▼
truncate_by_token_budget(≤4000)
    │
    ▼
naive_rag_response(prompt + chunks)
    │
    ▼
LLM Answer
```

### local — Entity-First

```
User Query
    │
    ▼
keywords_extraction → ll_keywords
    │
    ▼
entities_vdb.query(ll_keywords)
    │
    ▼
get_node() + node_degree()
    │
    ▼
1-hop neighbor expansion (get_node_edges)
    │
    ▼
related text_chunks lookup
    │
    ▼
truncate (≤4000 tokens) → rag_response
    │
    ▼
LLM Answer
```

### global — Relationship-First

```
User Query
    │
    ▼
keywords_extraction → hl_keywords
    │
    ▼
relationships_vdb.query(hl_keywords)
    │
    ▼
get_edge() + edge_degree()
    │
    ▼
endpoint entities → node_degree()
    │
    ▼
text_chunks linked to edges
    │
    ▼
truncate (≤4000 tokens) → rag_response
    │
    ▼
LLM Answer
```

### hybrid — Local + Global Merged

```
User Query
    │
    ▼
keywords_extraction
    │
    ├──────────────────────────────┐
    ▼                              ▼
local_query()                  global_query()
ll_keywords → entities      hl_keywords → relationships
→ entity context              → rel context
(≤4000 tokens)               (≤4000 tokens)
    │                              │
    └──────────┬───────────────────┘
               ▼
    process_combine_contexts()
    (deduplicate + merge CSV rows)
               │
               ▼
    mix_rag_response({kg_context})
               │
               ▼
           LLM Answer
```

### mix — KG + Vector Parallel Fusion

```
User Query
    │
    ├──────────────────────────────┐
    ▼                              ▼
get_kg_context()             get_vector_context()
keywords → graph traversal  chunks_vdb.query()
(≤4000 tokens)               (top_k=10)
    │                         │
    └──────────┬──────────────┘
               ▼
    mix_rag_response({kg_context}, {vector_context})
               │
               ▼
           LLM Answer
```

## Keyword Extraction (Shared Step)

All non-naive modes start with keyword extraction:

```python
keywords = await llm_model_func(
    prompt,
    system_prompt=keywords_extraction,
    keyword_extraction=True
)
# Returns: {"high_level_kw": [...], "low_level_kw": [...]}
```

| Keywords | Used In | Why |
|---|---|---|
| `high_level_keywords` | `global` mode | Broad conceptual search in relationship vectors |
| `low_level_keywords` | `local` mode | Specific entity matches |

**Example:** Query "What should I study to become a DevOps engineer?"
- hl_keywords: `["career", "study path", "devops", "learning"]` → finds relationships
- ll_keywords: `["NT548", "AWS", "Docker", "CI/CD"]` → finds specific entities

## Token Budget Defaults

| Mode | Budget | Parameter |
|---|---|---|
| All modes | `4000` tokens | `max_token_for_text_unit` |
| Global mode | `4000` tokens | `max_token_for_global_context` |
| Local mode | `4000` tokens | `max_token_for_local_context` |
| Mix mode vector | `4000` tokens | `max_token_for_text_unit` |

## Choosing a Mode

```
START HERE
  │
  ▼
Is the question about a specific entity?
  │
  ├─ YES → "Tell me about NT211"
  │         │
  │         ▼
  │       Use "local" mode
  │       (entity-first search)
  │
  └─ NO ↓
  │
  ▼
Is it about a broad topic or relationships?
  │
  ├─ YES → "How are CS courses connected?"
  │         │
  │         ▼
  │       Use "global" mode
  │       (relationship-first)
  │
  └─ NO ↓
  │
  ▼
Is it a simple factual lookup?
  │
  ├─ YES → "What is the deadline for HW1?"
  │         │
  │         ▼
  │       Use "naive" mode
  │       (pure vector, fastest)
  │
  └─ NO ↓
  │
  ▼
Is it complex / multi-faceted?
  │
  ├─ YES → "How should I plan my DevOps career?"
  │         │
  │         ▼
  │       Use "mix" mode
  │       (KG + vector, maximum recall)
  │
  └─ NO → Use "hybrid" (default)
```

## QueryParam

```python
param = QueryParam(
    mode="hybrid",
    top_k=60,                     # Results from vector search
    only_need_context=False,       # Return only context, skip LLM
    only_need_prompt=False,        # Return only built prompt
    stream=False,                  # Stream LLM response
    response_type="Multiple Paragraphs",
)
```

## Cache Behavior

All query modes check the LLM response cache before making an LLM call:
1. `compute_args_hash(mode, query, history)` → cache key
2. Exact match → return cached response
3. Embedding similarity (threshold 0.95) → optional LLM verification → return cached

Cache is disabled by `only_need_context=True` and `only_need_prompt=True`.
