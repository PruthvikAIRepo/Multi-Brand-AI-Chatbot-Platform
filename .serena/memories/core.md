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
- `mem:conventions` — coding/testing/deploy conventions.
- `mem:security_status` — open security issues (#3–#14) and what's fixed.
- `mem:memory_maintenance` — how to keep these memories healthy.

## Current build state (2026-06-25)
Foundation review complete. We are working **foundation-first, in user-journey order**,
starting with Super Admin/Admin auth so endpoints can be handed to the frontend dev.
**Unit 1 (login hardening) + Unit 2 (user-mgmt audit + unlock + hand-off doc) are DONE** —
see `mem:security_status`. Frontend reference: `docs/AUTH_API.md`. The Super-Admin/Admin auth
+ user-management surface is now ready to hand to the frontend dev. Nothing committed yet.
Next candidates: commit/branch this work, then either Unit 3 (the remaining OPEN issues in
`mem:security_status`, e.g. crypto #7 / Celery #6) or move forward in the journey.
