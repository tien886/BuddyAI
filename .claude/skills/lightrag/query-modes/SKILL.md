---
name: lightrag-query-modes
description: "Use when the user asks about query modes, how to choose a mode, or what the difference is between local/global/hybrid/naive/mix. Examples: 'What mode should I use?', 'How does hybrid mode work?', 'Difference between mix and naive?'"
---

# LightRAG — Query Modes

## Query Modes at a Glance

| Mode | Vector Search | KG Search | Context Building | Best For |
|---|---|---|---|---|
| `naive` | `chunks_vdb` (text chunk vectors) | ❌ None | Raw chunks only | Simple Q&A, pure semantic search |
| `local` | `entities_vdb` (entity vectors) | 1-hop from entities | Entity → rels → text chunks | "Tell me about [entity]" |
| `global` | `relationships_vdb` (rel vectors) | From edges | Edge → connected entities | "What relates to [topic]?" |
| `hybrid` | entities + relationships (both) | Both | Local + Global merged | Broad exploratory queries |
| `mix` | `chunks_vdb` (parallel) + KG (parallel) | Both | KG context + Vector context | Maximum recall, complex queries |

## Mode Comparison Detail

### naive — Pure Vector Search (No KG)
```
query → chunks_vdb.query() → get raw text chunks → naive_rag_response prompt → LLM
```
- No knowledge graph involved
- Fastest option
- Best: factoid Q&A on indexed docs, simple "find me content about X"

### local — Entity-First Search
```
query → ll_keywords → entities_vdb.query() → get_node() + degree() → 1-hop neighbors
→ text_chunks lookup → get_node_edges() → related edges → truncate by token budget
→ rag_response prompt → LLM
```
- Starts from **entities** found in text
- Good: "Who is NT211 taught by?", "What courses cover DevOps?"

### global — Relationship-First Search
```
query → hl_keywords → relationships_vdb.query() → get_edge() + degree()
→ extract endpoint entities → node_degree() → find text_chunks linked to edges
→ truncate → rag_response prompt → LLM
```
- Starts from **relationships** found in text
- Good: "What topics are covered in the ML track?", "How are courses connected?"

### hybrid — Local + Global Merged
```
query → ll_keywords → local_query() (entity context, ≤4000 tokens)
              + hl_keywords → global_query() (rel context, ≤4000 tokens)
       → combine_contexts() → deduplicate → mix_rag_response → LLM
```
- **Default mode** — best for most use cases
- Good: "Give me an overview of the DevOps career path"

### mix — Parallel KG + Vector Fusion
```
query → asyncio.gather(
    get_kg_context(),     # Keywords → KG traversal
    get_vector_context()  # chunks_vdb vector search (top_k=10)
  )
  → mix_rag_response with both {kg_context} + {vector_context} → LLM
```
- Runs KG and vector search **simultaneously**
- Highest recall — captures both structural knowledge and raw text
- Good: complex multi-faceted questions

## Keyword Extraction (All Non-Naive Modes)

Before any context building, LightRAG calls the LLM with `keywords_extraction` prompt:

```json
{
  "high_level_keywords": ["career", "devops", "study path"],
  "low_level_keywords": ["NT548", "AWS", "Docker"]
}
```

- `high_level_keywords` → used in **global** mode (relationships)
- `low_level_keywords` → used in **local** mode (entities)

**Why both?** A query like "How should I prepare for a DevOps career?" needs:
- `hl_keywords` = broad conceptual search in relationship vectors
- `ll_keywords` = specific entity matches (course codes, tools)

## Token Budgets

| Parameter | Default | Applies To |
|---|---|---|
| `max_token_for_text_unit` | `4000` | Local mode text chunks |
| `max_token_for_global_context` | `4000` | Global mode relationships |
| `max_token_for_local_context` | `4000` | Local mode entities |
| `max_token_for_text_unit` | `4000` | Mix mode vector chunks |

## Choosing a Mode

| Question Type | Recommended Mode |
|---|---|
| Simple factual lookup | `naive` |
| "Tell me about X entity" | `local` |
| "What topics/relationships exist?" | `global` |
| General exploratory query | `hybrid` (default) |
| Complex multi-faceted question | `mix` |
| When you need both raw text + KG | `mix` |

## QueryParam Config

```python
param = QueryParam(
    mode="hybrid",           # local/global/hybrid/naive/mix
    top_k=60,                # Results from vector/graph search
    only_need_context=False,  # Return only context, skip LLM
    only_need_prompt=False,  # Return only built prompt
    stream=False,            # Stream LLM response
    response_type="Multiple Paragraphs"  # Desired answer format
)
```
