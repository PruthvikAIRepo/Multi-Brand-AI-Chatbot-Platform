# Backend architecture

See `mem:core`. Layout under `backend/app/`:

- `api/v1/*.py` — thin route modules (one per resource). Aggregated in `api/v1/router.py`.
- `services/*.py` — business logic (the real work). 27 services. Routes should stay thin.
- `models/*.py` — SQLAlchemy ORM. `models/enums.py` holds all enums (UserRole, AdminActionType,
  ChannelType, SkinType, etc.). `models/logs.py` holds all 7 log tables incl. `AdminActivityLog`.
- `schemas/*.py` — Pydantic v2 request/response models.
- `core/` — cross-cutting: `permissions.py` (auth deps + RBAC), `security.py` (jwt/bcrypt),
  `encryption.py` (AES at rest), `cache.py`, `rate_limiter.py`, `exceptions.py`,
  `response.py` (uniform `{data, message, errors}` envelope), `request_utils.py` (client IP).
- `db/` — engine/session/base. `tasks/` — Celery. `middleware/` — **empty** (despite CLAUDE.md;
  security headers + handlers live inline in `main.py`).

## Request flow
`main.py` (CORS, security headers, exception handlers → uniform envelope)
→ `router.py` → route → `Depends(get_db)` + auth dependency → service → async SQLAlchemy.

## Auth dependency chain (see `mem:auth_and_rbac`)
`get_authenticated_user` (resolves JWT, lenient) → `get_current_user` (adds the
must-change-password gate) → `require_super_admin` / `require_brand_access` build on
`get_current_user`, so the whole admin surface inherits the gate. Public end-user routes
(chat, widget, ws_chat, webhooks, health) use NO auth dependency.

## Chat/RAG pipeline (single core: `chat_service.process_message`, used by REST + WebSocket)
moderation (before LLM) → get/create session conversation → update skin profile →
persist user msg → RAG retrieval (brand-scoped) → recommendation-rule filter + drop
already-recommended → assemble system prompt (tone + RAG context + session profile) →
LLM (try/except → brand fallback) → compliance filter → persist + update session state →
product cards → channel format. Known gaps in this pipeline are in `mem:security_status`.

## Multi-tenant model
`brands` is the tenant root. `user_brand_assignments` (user × brand, with a `permissions`
JSONB) maps Admins to brands. Content tables (products/faqs/routines/rules/configs/logs/leads)
all carry `brand_id`. Jobs-style global tables: none here — everything is brand-scoped except
the user/auth tables.
