# Deploying the backend to GCP (Cloud Run + Cloud SQL)

Target architecture:
- **Cloud Run** — runs the API container (`backend/Dockerfile`), scales to zero.
- **Cloud SQL for PostgreSQL 15** — the database; **pgvector** extension required
  (the schema has a `VECTOR(1024)` column).
- **Secret Manager** — holds `SECRET_KEY`, `ENCRYPTION_KEY`, `DATABASE_URL`, SMTP creds.
- **Memorystore (Redis)** — *optional*. Login works without it (the auth rate-limiter
  fails open); provision later for chat rate-limiting.

> Cost: Cloud SQL runs ~24/7 (smallest tier is a few $/mo); Cloud Run scales to zero.
> All charges land on the **client's** billing account — confirm before creating resources.

## 0. Fill these in
```
PROJECT_ID=<client-project-id>
REGION=<e.g. asia-south1 or us-central1>
INSTANCE=chatbot-pg
DB_NAME=chatbot
DB_USER=chatbot_app
CONN_NAME=$PROJECT_ID:$REGION:$INSTANCE     # instance connection name
gcloud auth login                            # the account with Editor on the client project
gcloud config set project $PROJECT_ID
```

## 1. Enable APIs
```
gcloud services enable run.googleapis.com sqladmin.googleapis.com \
  secretmanager.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

## 2. Cloud SQL (Postgres 15 + pgvector)
```
gcloud sql instances create $INSTANCE --database-version=POSTGRES_15 \
  --tier=db-custom-1-3840 --region=$REGION --storage-size=10GB
gcloud sql databases create $DB_NAME --instance=$INSTANCE
gcloud sql users create $DB_USER --instance=$INSTANCE --password='<STRONG_DB_PASSWORD>'
# Enable pgvector (run once, in the target DB):
gcloud sql connect $INSTANCE --user=postgres --database=$DB_NAME
#   then at the psql prompt:  CREATE EXTENSION IF NOT EXISTS vector;  \q
```

## 3. Secrets (Secret Manager)
Generate strong values (e.g. `python -c "import secrets;print(secrets.token_urlsafe(48))"`).
```
printf '%s' '<SECRET_KEY>'      | gcloud secrets create SECRET_KEY      --data-file=-
printf '%s' '<ENCRYPTION_KEY>'  | gcloud secrets create ENCRYPTION_KEY  --data-file=-
# DATABASE_URL uses the Cloud SQL unix socket that Cloud Run mounts:
printf '%s' 'postgresql+asyncpg://'"$DB_USER"':<STRONG_DB_PASSWORD>@/'"$DB_NAME"'?host=/cloudsql/'"$CONN_NAME" \
  | gcloud secrets create DATABASE_URL --data-file=-
# (optional) SMTP_PASSWORD, etc.
```
Grant the Cloud Run runtime service account access (defaults to the compute SA):
```
PNUM=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
SA="$PNUM-compute@developer.gserviceaccount.com"
for s in SECRET_KEY ENCRYPTION_KEY DATABASE_URL; do
  gcloud secrets add-iam-policy-binding $s --member="serviceAccount:$SA" \
    --role=roles/secretmanager.secretAccessor
done
```

## 4. Deploy to Cloud Run (builds from source via Cloud Build)
```
gcloud run deploy chatbot-api \
  --source backend \
  --region $REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances $CONN_NAME \
  --set-env-vars ENVIRONMENT=production,CORS_ORIGINS=https://admin.yourbrand.com \
  --set-secrets SECRET_KEY=SECRET_KEY:latest,ENCRYPTION_KEY=ENCRYPTION_KEY:latest,DATABASE_URL=DATABASE_URL:latest
```
The fail-closed config guard will refuse to boot if `SECRET_KEY`/`ENCRYPTION_KEY` are
missing or default — that's expected and good.

## 5. Run migrations + seed (one-off, via Cloud SQL Auth Proxy)
```
# download the proxy: https://cloud.google.com/sql/docs/postgres/sql-proxy
./cloud-sql-proxy $CONN_NAME --port 5432 &      # listens on 127.0.0.1:5432
cd backend
export DATABASE_URL='postgresql+asyncpg://'"$DB_USER"':<STRONG_DB_PASSWORD>@127.0.0.1:5432/'"$DB_NAME"
export ENVIRONMENT=development                  # seed/migrate don't need prod secrets
venv/Scripts/python.exe -m alembic upgrade head
SUPERADMIN_EMAIL=<owner@brand.com> SUPERADMIN_PASSWORD=<Strong#Pass> venv/Scripts/python.exe -m app.seed
```
(Alternatively run these as a Cloud Run **Job** using the same image + `--add-cloudsql-instances`.)

## 6. Verify
```
URL=$(gcloud run services describe chatbot-api --region $REGION --format='value(status.url)')
curl -s $URL/api/v1/health            # -> {"status":"healthy",...}
curl -s $URL/docs -o /dev/null -w '%{http_code}\n'   # Swagger
# then exercise /api/v1/auth/login with the seeded Super Admin (see docs/AUTH_API.md)
```

## 7. Post-launch
- Point the admin frontend domain; update `CORS_ORIGINS` (redeploy or `gcloud run services update`).
- Configure SMTP secrets so password-reset / invite emails send.
- Provision Memorystore (Redis) and set `REDIS_URL` when enabling chat rate-limiting.
- Rotate `ENCRYPTION_KEY` later via `ENCRYPTION_KEYS_RETIRED` (see `mem:encryption`).
