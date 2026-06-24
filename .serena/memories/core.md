# Core — entry point

Read this first, then follow `mem:NAME` references to focused memories.

## What this project is
**Multi-Brand AI Chatbot Platform** for skincare brands. One admin dashboard manages
independent, fully-isolated chatbot instances per brand. AI engine = Claude/OpenAI
(provider-agnostic) + RAG over each brand's products/FAQs/routines. Channels: Website
(WebSocket) in Phase 1; WhatsApp + Instagram in Phase 2. Developer: Keshav Infotech.

- Repo: `PruthvikAIRepo/Multi-Brand-AI-Chatbot-Platform` (branch `main`).
- Backend lives in `backend/` (FastAPI, async). Frontend (React admin + widget) not in this repo yet.
- Source-of-truth docs at repo root: `SCOPE_OF_WORK.md`, `CLIENT_REQUIREMENTS.md`,
  `DATABASE_DESIGN.md`, `UI_SCREENS_SPECIFICATION.md`, `SRS_Multi_Brand_AI_Chatbot_Complete_Final.pdf`,
  `CLAUDE.md`. The SRS PDF is the ultimate authority (§21 = roles/auth/RBAC).

## The #1 architectural rule
**Brand isolation.** Every brand-scoped query MUST filter `brand_id`. There is **NO
Postgres RLS** — isolation is purely application-layer, so a missing filter = cross-tenant
leak. (Verified: the content-CRUD layer does this correctly via `(id, brand_id)` predicates.)

## Focused memories
- `mem:tech_stack` — stack, how to run, how to test.
- `mem:architecture_backend` — backend layout and how requests flow.
- `mem:auth_and_rbac` — Super Admin / Admin model, permissions, login flow (current).
- `mem:encryption` — at-rest encryption (AES-256-GCM) + key rotation + secret handling.
- `mem:conventions` — coding/testing/deploy conventions.
- `mem:security_status` — open security issues (#3–#14) and what's fixed.
- `mem:memory_maintenance` — how to keep these memories healthy.

## Current build state (2026-06-25)
Foundation review complete. We are working **foundation-first, in user-journey order**,
starting with Super Admin/Admin auth so endpoints can be handed to the frontend dev.
**Unit 1 (login hardening) + Unit 2 (user-mgmt audit + unlock + hand-off doc)** are merged to
`main` (PR #15). Frontend reference: `docs/AUTH_API.md`. **Unit 3 (at-rest encryption, #7)** is
implemented on `feature/encryption-hardening` (see `mem:encryption`). See `mem:security_status`
for what's done vs the remaining OPEN issues (#4, #6, #10–#14).
