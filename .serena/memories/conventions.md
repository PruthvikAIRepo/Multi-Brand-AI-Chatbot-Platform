# Conventions & workflow

See `mem:core`.

## Code
- Async throughout (`async def`, awaited DB calls). Pydantic v2 schemas. Type hints expected.
- Routes thin; logic in `services/`. Custom exceptions in `core/exceptions.py` map to HTTP
  status; responses use the `{data, message, errors}` envelope (`core/response.py`).
- **Every brand-scoped query MUST filter `brand_id`** (no RLS — app-layer isolation). When
  fetching/updating/deleting by id, constrain `(id, brand_id)`, never bare PK.
- Mass-assignment: use explicit field allowlists on updates (product/brand do; the 4
  brand-config updaters use blind `setattr` — flagged in `mem:security_status` #14).
- Emails: always normalize to `.strip().lower()` at storage and lookup.
- Alembic for schema changes (never raw DDL in code). Single migration chain today.

## Secrets / config
- All config in `app/config.py` (pydantic-settings). Real secrets via env / `backend/.env`
  (gitignored). Never commit real keys. Production MUST set `ENVIRONMENT=production` (activates
  the fail-closed guard). Secrets/PII are AES-encrypted at rest and never returned decrypted.

## Testing
- pytest + pytest-asyncio (`asyncio_mode=auto`), config in `backend/pytest.ini`, tests in
  `backend/tests/`. Dev deps in `backend/requirements-dev.txt`.
- Run: `cd backend && venv/Scripts/python.exe -m pytest`.
- Prefer fast unit tests that mock the DB session (see `tests/test_authenticate_user.py`'s
  `FakeSession`) since there's no local pgvector Postgres. Each test's docstring should state
  the bug it guards against.
- Known import-time noise: passlib/bcrypt-4.x "error reading bcrypt version" (harmless).

## Git / GitHub
- Branch per ticket: `feature/{issue}-short-desc`; PR to `main`. Issues track bugs/work
  (labels include `bug`, `security`, `enhancement`). Confirmed bugs from review = #3–#14.
- Only commit/push when the user asks.

## Working style with the owner (Pruthvik)
- Foundation-first, in user-journey order; small reviewable units; pause for review between
  units. Verify changes by compile + import + tests before declaring done. Update these
  memories in the same change (see `mem:memory_maintenance`).
