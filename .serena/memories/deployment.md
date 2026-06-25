# Deployment

See `mem:core`. Target: **GCP** (client's project; owner has Editor role).

## Artifacts (in repo)
- `backend/Dockerfile` — python:3.13-slim, non-root, gunicorn + uvicorn workers, honors `$PORT`.
- `backend/.dockerignore` — excludes `.env`, `venv`, tests, caches.
- `backend/.env.example` — all settings with placeholders.
- `docs/DEPLOY_GCP.md` — full runbook (Cloud Run + Cloud SQL + Secret Manager).
- `.github/workflows/ci.yml` — runs pytest on PRs/main (no deploy step).

## GCP architecture
- **Cloud Run** runs the API container (scales to zero).
- **Cloud SQL for PostgreSQL 15** — DB; **pgvector required** (schema has a `VECTOR(1024)`
  column → `CREATE EXTENSION vector` before `alembic upgrade head`).
- **Secret Manager** — `SECRET_KEY`, `ENCRYPTION_KEY`, `DATABASE_URL` (+ SMTP later).
- **Memorystore (Redis)** — optional; login works without it (auth limiter fails open).

## Release steps
1. `gcloud run deploy chatbot-api --source backend --add-cloudsql-instances <CONN> --set-secrets ...`
2. Migrate + seed once via Cloud SQL Auth Proxy (or a Cloud Run Job): `alembic upgrade head`
   then `python -m app.seed` with `SUPERADMIN_EMAIL/PASSWORD`.
3. Verify `/api/v1/health` and `/docs`.

## Gotchas
- App is **fail-closed**: must set `ENVIRONMENT=production` + real `SECRET_KEY`/`ENCRYPTION_KEY`
  or it refuses to boot.
- The local gcloud is authed as `pruthvikchandaranaa@gmail.com`; the **client project id +
  the Editor account + region** must be supplied before deploying. I never enter the owner's
  Google password — the owner runs `gcloud auth login`; I drive the deploy commands.
- DATABASE_URL on Cloud Run uses the unix socket: `...@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE`.
- No CI deploy step — deploys are manual/gated (matches the careful, owner-driven workflow).
