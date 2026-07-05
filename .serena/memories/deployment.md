# Deployment

## LIVE (2026-07-04) ✅
- **Service:** Cloud Run `chatbot-api`, region `us-central1`, project `anurion-ai-platform`.
- **URL:** https://chatbot-api-721332751968.us-central1.run.app  (Swagger at `/docs`).
- **DB:** Cloud SQL `chatbot-pg` (Postgres 15, db-f1-micro), DB `chatbot`, pgvector 0.8.1,
  schema migrated (`7c8ed624ae89`), Super Admin seeded (`kinnrisoni777@gmail.com`, must-change).
- **Config:** injected as Cloud Run **env vars** (ENVIRONMENT=production, SECRET_KEY,
  ENCRYPTION_KEY, DATABASE_URL socket form, CORS_ORIGINS=*). NOT in Secret Manager (see IAM note).
- **Verified live:** `/health` db=ok (redis=error, expected — no Memorystore; login fails open),
  `/docs`=200, `/auth/login` works (must_change_password=true).
- **IAM:** `kinnrisoni777@gmail.com` is now **Owner** (accepted the invite). Runtime/compute SA
  granted cloudsql.client + cloudbuild.builds.builder + storage.admin + logging.logWriter +
  artifactregistry.writer. Future deploys need no new access.

## Redeploy
`gcloud run deploy chatbot-api --source backend --region us-central1 --add-cloudsql-instances
anurion-ai-platform:us-central1:chatbot-pg` (env vars are retained across deploys; omit
--env-vars-file unless changing them). Needs `backend/.gcloudignore` (excludes venv) present.

## Open follow-ups (optional, non-blocking)
- `backend/.gcloudignore` is created locally but **not yet committed** — commit it so redeploys stay lean.
- Lock CORS to the real admin-frontend domain when known (currently `*`).
- Add Memorystore (Redis) + set REDIS_URL before enabling chat rate-limiting.
- Move secrets from Cloud Run env → Secret Manager once a least-privilege runtime SA is set up
  (now possible with Owner; was blocked under Editor).

---

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
