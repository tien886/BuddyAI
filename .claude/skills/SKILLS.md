# Skills Index

## lightrag — RAG & Knowledge Graph

| Task | Skill to Read |
|------|---------------|
| How LightRAG works / architecture | `skills/lightrag/architecture/SKILL.md` |
| Query modes (local/global/hybrid/mix/naive) | `skills/lightrag/query-modes/SKILL.md` |
| Storage backends (JsonKV, NanoVectorDB, NetworkX, Neo4j...) | `skills/lightrag/storage/SKILL.md` |
| Indexing pipeline (chunk → entity extract → upsert) | `skills/lightrag/indexing/SKILL.md` |
| Prompt engineering guide | `skills/lightrag/prompts/SKILL.md` |
| Common issues & troubleshooting | `skills/lightrag/troubleshooting/SKILL.md` |

## backend — UIT Buddy Backend Proxy

| Task | Skill to Read |
|------|---------------|
| How backend proxy works / auth flow | `skills/backend/architecture/SKILL.md` |
| Calendar service (/api/schedule) | `skills/backend/calendar/SKILL.md` |
| Document service (/api/document) | `skills/backend/document/SKILL.md` |
| User service (/api/user) | `skills/backend/user/SKILL.md` |

## Quick-Start by Question Type

- **"How does LightRAG index a document?"** → `skills/lightrag/indexing/SKILL.md`
- **"What query mode should I use?"** → `skills/lightrag/query-modes/SKILL.md`
- **"How do I swap NetworkX for Neo4j?"** → `skills/lightrag/storage/SKILL.md`
- **"Why is extraction missing entities?"** → `skills/lightrag/troubleshooting/SKILL.md`
- **"How do I customize entity extraction?"** → `skills/lightrag/prompts/SKILL.md`
- **"How does the backend proxy work?"** → `skills/backend/architecture/SKILL.md`
- **"How do I add a new backend endpoint?"** → `skills/backend/calendar/SKILL.md` (as template)
- **"What's the end-to-end flow?"** → `context-memory/DATA_FLOW.md`
- **"How does BuddyAI route questions?"** → `context-memory/BUDDYAI_DECISION_GATE.md`
- **"What does the server expose?"** → `context-memory/PROJECT_OVERVIEW.md`