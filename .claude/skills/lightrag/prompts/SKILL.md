---
name: lightrag-prompts
description: "Use when the user asks about LLM prompts in LightRAG, wants to customize entity extraction, or needs to modify prompt behavior. Examples: 'How do I customize entity extraction?', 'Change the response format', 'Add my own entity types'"
---

# LightRAG — Prompt Engineering Guide

## Overview

All prompts live in `lightrag/prompt.py`. They're **language-aware**, **delimiter-aware**, and support **few-shot examples**.

## All Prompts

| Prompt Key | Stage | Tells LLM To |
|---|---|---|
| `entity_extraction` | Indexing | Extract entities + relationships from a text chunk |
| `entity_extraction_examples` | Indexing | 3 few-shot examples for entity extraction |
| `summarize_entity_descriptions` | Indexing | Merge multiple descriptions into one |
| `entiti_continue_extraction` | Indexing | Ask for missed entities (gleaning loop) |
| `entiti_if_loop_extraction` | Indexing | YES/NO check for more entities |
| `keywords_extraction` | Querying | Extract hl + ll keywords from user query |
| `keywords_extraction_examples` | Querying | 3 few-shot examples for keyword extraction |
| `rag_response` | Querying | Answer from KG context (local/global) |
| `naive_rag_response` | Querying | Answer from raw text chunks only |
| `mix_rag_response` | Querying | Fuse KG + vector context into answer |
| `similarity_check` | Cache | Judge semantic similarity of two questions |

## Key Constants

```python
GRAPH_FIELD_SEP = "<SEP>"          # Separator between multiple source IDs
DEFAULT_ENTITY_TYPES = ["organization", "person", "geo", "event", "category"]
DEFAULT_TUPLE_DELIMITER = "<|>"    # Separates fields in entity/relationship tuples
DEFAULT_RECORD_DELIMITER = "##"    # Separates one entity/rel from the next
DEFAULT_COMPLETION_DELIMITER = "<|COMPLETE|>"  # Signals end of extraction
```

## Customizing Entity Extraction

### Change Entity Types

Pass `entity_types` in `addon_params`:

```python
rag = LightRAG(
    ...
    addon_params={
        "language": "Simplified Chinese",
        "entity_types": ["course", "skill", "tool", "certification", "concept"]
    }
)
```

### Modify the Extraction Prompt

Edit `prompt.py` directly:

```python
entity_extraction = """...
Your task is to identify the entities and relationships...

## Entity Types
- organization
- person
...

## Output Format
##entity_name<|>entity_type<|>entity_description##
##source_entity<|>target_entity<|>relationship_description<|>strength<|>keywords##
...
"""
```

### Add Custom Few-Shot Examples

Edit `entity_extraction_examples` in `prompt.py`:

```python
examples = """
Example 1:
Input: "NT548 is a DevOps course taught by Dr. Smith. Students learn Docker, Kubernetes, and CI/CD pipelines."
Output:
##NT548<|>course<|>DevOps course covering containerization and CI/CD##
##Dr. Smith<|>person<|>Professor teaching NT548##
##Docker<|>tool<|>Containerization tool covered in NT548##
##NT548<|>Dr. Smith<|>taught_by<|>high<|>DevOps, course, professor##
##NT548<|>Docker<|>uses<|>high<|>DevOps, containerization##
...
"""
```

## Keyword Extraction Prompt

Extracts two types of keywords from the user query:

```json
{
  "high_level_keywords": ["career", "study path", "devops"],
  "low_level_keywords": ["NT548", "AWS", "Docker", "Kubernetes"]
}
```

**`high_level_keywords`** → `global` mode (relationships) — broad conceptual search
**`low_level_keywords`** → `local` mode (entities) — specific entity matches

Customize by editing `keywords_extraction` in `prompt.py`. The prompt instructs the LLM to output valid JSON.

## Response Prompts

### `naive_rag_response` — Pure Vector Search
```
Answer the user question based on the given context.
If there is no relevant information in the provided context, say "I don't know."
...
```

### `rag_response` — KG Context
```
You are a helpful assistant...
You have been provided with a knowledge graph...
[Entities]
[Relationships]
[Sources]
Answer the user question based on the above knowledge graph...
```

### `mix_rag_response` — KG + Vector Fusion
```
You are a helpful assistant...
You have been provided with a knowledge graph and retrieved information...
[Knowledge Graph]
[Retrieved Information]
Combine both sources to give a comprehensive answer...
```

### Response Type

`QueryParam.response_type` controls desired answer format:
- `"Multiple Paragraphs"` (default)
- `"Single Paragraph"`
- `"Multiple Choices"`
- `"Buterfly"`
- etc.

## Language Configuration

Pass language via `addon_params`:

```python
addon_params={"language": "Simplified Chinese"}
```

This is substituted into entity extraction and response prompts to guide the LLM's output language.

## Prompt Injection Safety

LightRAG does **not** currently sanitize prompt inputs. If accepting user-provided text for indexing, be aware that:
1. The entity extraction prompt includes raw text from the document
2. Malformed output from the LLM is handled by regex parsing with fallback
3. Consider validating/sanitizing document content before indexing if your use case requires it
