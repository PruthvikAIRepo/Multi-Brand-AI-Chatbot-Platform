# Tech stack & commands

See `mem:core` for the project overview.

## Stack
- **Web:** FastAPI (async), Starlette. Entry: `backend/app/main.py` (`create_app()`), routes
  aggregated in `backend/app/api/v1/router.py` under prefix `/api/v1`.
- **DB:** PostgreSQL + **pgvector**. Async SQLAlchemy 2.x (`asyncpg`). Single engine +
  `async_sessionmaker` in `backend/app/db/session.py`; `get_db` commits on success / rolls
  back on raised exception. Models use UUID PKs + `created_at/updated_at` mixins (`db/base.py`).
- **Migrations:** Alembic. Currently a **single** migration
  `backend/alembic/versions/7c8ed624ae89_initial_schema_with_permissions.py`.
- **Task queue:** Celery + Redis (`backend/app/tasks/`). NOTE: embedding tasks exist but are
  **not actually dispatched** — see `mem:security_status` (#6).
- **LLM:** provider-agnostic (`app/services/llm_service.py`). Config default = OpenAI
  `gpt-4o-mini`; Anthropic Claude ready to swap (client will provide key). CLAUDE.md says
  "Claude Sonnet" — launch default is a decision to confirm.
- **Embeddings:** OpenAI or Voyage (config-selectable). Vector search currently scans all of
  a brand's embeddings in NumPy (works, but won't scale — #14).
- **Auth:** JWT HS256 (access 30m) + hashed refresh tokens; bcrypt via passlib.
- **Storage:** AWS S3 (`app/services/s3_service.py`). Email via SMTP.

## Local dev
- Virtualenv: `backend/venv` (use `backend/venv/Scripts/python.exe` on Windows).
- Config: `backend/.env` (gitignored) provides real `SECRET_KEY`/`ENCRYPTION_KEY`/`ENVIRONMENT`.
  `ENVIRONMENT` defaults to `development`; **production deploys must set ENVIRONMENT=production**
  (this activates the fail-closed secret guard in `config.py`).
- Seed first Super Admin: `SUPERADMIN_EMAIL=... SUPERADMIN_PASSWORD=... python -m app.seed`
  (fails closed if creds missing/weak; account is forced to change password on first login).

## Tests
- `pip install -r backend/requirements-dev.txt` (pytest + pytest-asyncio).
- Run: `cd backend && venv/Scripts/python.exe -m pytest` (config in `backend/pytest.ini`,
  `asyncio_mode=auto`). Tests live in `backend/tests/`.
- Note: a harmless passlib/bcrypt-4.x "error reading bcrypt version" line prints on import;
  bcrypt still works. Consider pinning bcrypt<4.1 or upgrading passlib (`mem:conventions`).
