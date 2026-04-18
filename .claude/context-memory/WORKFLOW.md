# BuddyAI Workflow (Refined Demo Version)

## Overview

This workflow describes how BuddyAI processes user requests efficiently by:

* filtering unnecessary heavy processing
* retrieving only relevant data
* using LightRAG for knowledge reasoning
* using LLM (Gemini) for explanation
* avoiding unnecessary n8n execution

The system is designed to be:

* efficient (avoid over-triggering n8n)
* grounded (based on real data)
* flexible (handle different types of questions)

---

## High-Level Flow

```text
User
  ↓
Decision Gate
  ↓
[fast | lookup | thinking]
  ↓
Execution Layer
  ↓
LLM (optional)
  ↓
Response
```

---

## Step-by-Step Workflow

### 1. User sends a request

Example:

> "What is the weather today?"
> "What is NT211?"
> "I want to become a DevOps engineer, what should I study?"

---

## 2. Decision Gate (Critical Layer)

This is the most important part of the system.

BuddyAI determines:

* Is this question relevant to the system?
* Does it require data retrieval?
* Does it require reasoning?

---

### 2.1 Domain Check

Check if the question belongs to BuddyAI scope:

**In-domain:**

* courses
* schedules
* deadlines
* academic planning
* career-related study paths

**Out-of-domain:**

* weather
* news
* general knowledge

Example:

```json
{
  "mode": "out_of_domain",
  "action": "skip_all"
}
```

👉 No backend, no LightRAG, no n8n

---

### 2.2 Complexity Classification

If the question is in-domain, classify into:

#### A. Fast

* no external data needed
* no reasoning required

Examples:

* hello
* summarize this text

Action:
→ answer directly

---

#### B. Lookup

* requires retrieving facts
* no multi-step reasoning

Examples:

* what is NT211
* what deadlines do I have today
* what is my schedule tomorrow

Action:
→ call backend OR LightRAG (no n8n)

---

#### C. Thinking

* requires reasoning, planning, or recommendation

Examples:

* recommend courses for DevOps
* compare courses
* plan my semester

Action:
→ trigger full pipeline (n8n + LLM + LightRAG)

---

## 3. Execution Layer

Based on decision:

---

### 3.1 Fast Path

```text
User → direct response
```

No:

* backend
* LightRAG
* n8n

---

### 3.2 Lookup Path

```text
User → Backend / LightRAG → Response
```

Used for:

* course info
* schedules
* prerequisites

---

### 3.3 Thinking Path (Full Pipeline)

```text
User
  ↓
BuddyAI
  ↓
Validate Access
  ↓
Backend (user data)
  +
Knowledge Graph (LightRAG)
  ↓
Context Builder
  ↓
n8n Workflow
  ↓
Gemini (LLM)
  ↓
Response
```

---

## 4. Data Sources

### 4.1 Backend (UIT Buddy Backend)

Provides:

* schedules
* deadlines
* enrolled courses
* student context

---

### 4.2 Knowledge Graph (LightRAG)

Built from:

* course data
* policy documents

Provides:

* prerequisites
* course relationships
* topics
* academic rules

---

## 5. Context Builder

Before calling LLM, BuddyAI:

* merges backend + KG results
* removes duplicates
* resolves conflicts
* labels uncertainty (e.g. outdated description)
* formats structured input

---

## 6. LLM (Gemini)

Used ONLY for:

* explanation
* recommendation
* summarization

NOT for:

* factual source of truth

---

## 7. Response Generation

BuddyAI returns:

* clear answer
* grounded in retrieved data
* with uncertainty if needed

Example:

> Based on your goal of becoming a DevOps engineer, you should take NT548 and related cloud courses. This recommendation is based on course relationships and prerequisites.

---

## Key Design Principles

### 1. Never over-trigger n8n

n8n runs ONLY for:

* thinking questions

---

### 2. Separate concerns

| Layer         | Responsibility  |
| ------------- | --------------- |
| Decision Gate | route question  |
| Backend       | user data       |
| LightRAG      | knowledge graph |
| LLM           | explanation     |

---

### 3. Prefer cheap paths first

Priority:

1. fast
2. lookup
3. thinking (most expensive)

---

### 4. Domain awareness is critical

Out-of-domain questions must NOT trigger:

* backend
* LightRAG
* n8n

---

## One-line Summary

BuddyAI first decides whether a question is relevant and complex, then only uses heavy components (LightRAG, n8n, LLM) when necessary, ensuring efficient and accurate responses.
