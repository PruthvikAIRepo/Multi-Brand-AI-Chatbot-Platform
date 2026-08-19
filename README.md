# Multi-Brand AI Chatbot Platform

**One admin dashboard, N fully-isolated AI chatbots — each brand gets its own knowledge base, tone, compliance rules and vector namespace.**

A multi-tenant chatbot platform for skincare brands. The AI engine uses the Claude API (Sonnet) with RAG over brand-isolated pgvector namespaces to deliver grounded, brand-accurate, compliance-filtered answers across Website chat (Phase 1), WhatsApp and Instagram DM (Phase 2).

## Architecture

Channels (Web widget / WhatsApp / Instagram) → Channel Router → **FastAPI request pipeline per brand:** Input Moderation → Brand Config → Rules Engine → RAG Retrieval (pgvector, <500ms) → Claude API (Sonnet) → Compliance Filter → Response. Backed by PostgreSQL + pgvector, Celery + Redis, AWS S3.

## What makes it production-grade

- **Multi-tenant isolation, three layers deep** — row-level brand_id filtering on every query, dedicated pgvector namespaces per brand, brand-scoped RBAC with full audit logging.
- **Hallucination control** — responses strictly grounded to the brand knowledge base; configurable similarity threshold; safe brand-tone fallback when no grounded answer exists.
- **Compliance engine** — no medical claims, admin-defined blocked phrases, approved-ingredient answers only; all rules take effect live, no restart.
- **Prompt-injection defense** — pattern matching, instruction sandboxing, role lock, off-topic classifier, spam/abuse filters, per-brand sensitivity.
- **Tone & personality engine** — per-brand vocabulary, emotional style, response-length modes, micro-tone rules.
- **Recommendation rules engine** — skin-type & concern mapping, priority scores, exclusion and conflict rules (e.g. retinol × vitamin C), rule simulator, CSV bulk import.
- **Security** — AES-256 encrypted per-brand API keys, JWT + bcrypt auth, brute-force lockout, honeypots + reCAPTCHA v3.
- **Observability** — conversation, RAG-retrieval (chunks + similarity scores), error, compliance, moderation and admin-activity logs.
- **Cost control** — per-brand token caps, per-user rate limits, per-brand API consumption tracking.

## Stack

| Layer | Technology |
| --- | --- |
| Backend API | Python / FastAPI |
| AI / LLM | Claude API (Sonnet) via Anthropic SDK |
| Vector search | pgvector (PostgreSQL), brand-isolated namespaces |
| Task queue | Celery + Redis |
| Admin panel | React + Tailwind CSS |
| Chat widget | React embeddable, WebSocket, reCAPTCHA v3 |
| Storage | PostgreSQL (27 tables) + AWS S3 |
| CI | Backend unit tests on every PR and push to main |

## Repo contents

- `backend/` — FastAPI application
- `docs/`, `DATABASE_DESIGN.md`, `UI_SCREENS_SPECIFICATION.md` — full engineering docs
- `SCOPE_OF_WORK.md` — complete Phase 1 / Phase 2 scope (28 + 10 deliverables)
- `SRS_*.pdf` — full software requirements specification

---

Built by [Pruthvik Chandarana](https://github.com/PruthvikAIRepo) — AI + backend engineer. Live RAG demo: [codefirstai.com](https://codefirstai.com/) (click the chat bubble).
