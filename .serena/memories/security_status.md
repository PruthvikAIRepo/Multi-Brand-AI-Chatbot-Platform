# Security status & open issues

From the foundation review (2026-06). GitHub issues #3–#14 (labels `bug`,`security`).

## DONE (working tree; not yet committed) — Step 1 + Unit 1
- **Seed backdoor removed** — `app/seed.py` now reads `SUPERADMIN_EMAIL`/`SUPERADMIN_PASSWORD`
  from env, fails closed, validates strength, never prints the password. (Old hardcoded
  `admin@chatbot.com / Admin@123` is gone.)
- **must_change_password is now enforced** — `permissions.py` split into
  `get_authenticated_user` (lenient escape hatch) + `get_current_user` (enforced gate).
- **#3 lockout fixed** — failed attempts committed before raise (was flushed → rolled back).
- **#9 timing oracle fixed** — dummy bcrypt verify on unknown-email path.
- **#8 auth rate limiting added** — per-IP on login/forgot/reset, fails open on Redis outage.
- **#5 fail-closed config** — app refuses to boot in non-dev with default/empty
  `SECRET_KEY`/`ENCRYPTION_KEY`; `ENVIRONMENT` now defaults to `development`.
- **Audit IP capture** — `core/request_utils.get_client_ip` (X-Forwarded-For aware); LOGIN /
  FAILED_LOGIN audited with IP.
- Covered by `backend/tests/` (17 passing). See `mem:conventions`.

### Unit 2 (user management + audit)
- All user-mgmt actions (invite/brands/permissions/deactivate/activate) now audited with
  **IP + before/after state** (SRS §21.3). Invite logs the new user id.
- New **`POST /users/{id}/unlock`** (Super Admin) to clear a lockout.
- `invite_user` lowercases email (consistency with login; prevents mixed-case lockout).
- Frontend hand-off doc: `docs/AUTH_API.md`.

## OPEN — still to do
- **#4 CRITICAL** — Meta webhook signature verification is bypassed when `META_APP_SECRET`
  empty (default), no env gate. (Phase 2 channel; fix before enabling webhooks.)
- **#6 CRITICAL** — embeddings are NOT dispatched to Celery; they run inline in the request.
  Tasks in `app/tasks/embedding_tasks.py` are dead code (never `.delay()`'d).
- **#7 HIGH** — AES-CBC with no auth tag, unsalted SHA-256 key derivation, no key rotation.
  Move to Fernet/AES-GCM + versioned key.
- **#10 HIGH** — upload stored-XSS: client-trusted content-type, SVG allowed, public S3 URLs.
- **#11 HIGH** — webhooks not idempotent (Meta retries → duplicate replies); batches dropped.
- **#12 HIGH** — "instant override" broken: prompt publish/restore + compliance-rule edits
  don't invalidate the cached system prompt (`system_prompt:{brand_id}`, 300s TTL).
- **#13 HIGH** — global (NULL-brand) block-list dedup broken (`== None`; NULL-distinct unique).
- **#14 MEDIUM cluster** — no hard fallback on empty RAG (hallucination); compliance skipped
  on LLM-error branch; unbounded NumPy vector scan; blind setattr mass-assignment in
  brand-config updaters; broadcast notification mark-read mutates shared row; invite defaults
  to all 32 perms (least-privilege); no refresh-token rotation; temp password echoed in invite
  response; lead CSV export not audit-logged; `asyncio.run()` per Celery task.

## Verdict
Brand isolation, RBAC lockdown (user/secret mgmt = Super-Admin-only, live role re-read),
moderation-before-LLM, and session memory are solid. Risk concentrates in auth resilience
(now largely fixed), secrets-at-rest crypto (#7), and "infra that looks built but isn't
wired" (Celery #6, webhook signing #4).
