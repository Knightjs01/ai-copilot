# Deploying to Railway

This walks through taking the app from local Docker Compose to a live Railway deployment
with two independent logins sharing one company's data. It assumes you already have a
[Railway](https://railway.app) account and the repo pushed to GitHub.

Everything Railway needs to build and run the services (`backend/Dockerfile`'s `production`
stage, `backend/railway.toml`) is already committed. This doc is the manual part — the
account, project, and environment variables only you can create.

## 1. Generate fresh production secrets

Never reuse the values from your local `backend/.env`. Generate new ones:

```bash
python -c "import secrets; print(secrets.token_urlsafe(24))"   # APP_DB_PASSWORD
python -c "import secrets; print(secrets.token_urlsafe(24))"   # AUTH_DB_PASSWORD
python -c "import secrets; print(secrets.token_urlsafe(64))"   # SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # ENCRYPTION_KEY
```

Save these somewhere safe (password manager) — you'll paste them into Railway in step 3.

## 2. Create the Railway project

1. New Project → Deploy from GitHub repo → select this repo.
2. Add a **Postgres** plugin (Railway provisions it and exposes connection details).
3. Add a **Redis** plugin.

Railway will try to auto-detect a service from the repo root — delete that auto-created
service once added; you'll add the backend and frontend explicitly in steps 3–4, each
pointed at its own subdirectory.

## 3. Add the backend service

New service → this repo → set **root directory** to `backend/`. Railway will pick up
`backend/railway.toml` automatically (Dockerfile build, `production` target, health check
at `/api/v1/health`).

**Add a Volume** mounted at `/app/storage` — without this, uploaded resumes vanish on every
redeploy (the storage backend is local-filesystem, see `backend/app/core/config.py`'s
`storage_dir` comment).

Set these environment variables on the backend service:

| Variable | Value |
|---|---|
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | `postgresql+asyncpg://app_runtime:<APP_DB_PASSWORD>@<postgres-host>:<port>/<db>` (host/port/db from the Postgres plugin's connection info) |
| `AUTH_DATABASE_URL` | `postgresql+asyncpg://app_auth:<AUTH_DB_PASSWORD>@<postgres-host>:<port>/<db>` |
| `MIGRATION_DATABASE_URL` | the Postgres plugin's own `DATABASE_URL` (bootstrap superuser — this is what actually creates the `app_runtime`/`app_auth` roles on first migration) |
| `APP_DB_PASSWORD` | from step 1 |
| `AUTH_DB_PASSWORD` | from step 1 |
| `REDIS_URL` | the Redis plugin's connection URL |
| `SECRET_KEY` | from step 1 |
| `ENCRYPTION_KEY` | from step 1 |
| `ANTHROPIC_API_KEY` | your key from console.anthropic.com |
| `BREVO_API_KEY` | your Brevo API key |
| `BREVO_SENDER_EMAIL` | a sender verified in your Brevo account (see step 6) |
| `COOKIE_SECURE` | `true` |
| `STORAGE_DIR` | `/app/storage` |
| `CORS_ORIGINS` | placeholder for now (`http://localhost:3000`) — you'll fix this in step 5 |
| `FRONTEND_BASE_URL` | same placeholder, same fix in step 5 |

Deploy. On first boot the container runs `alembic upgrade head` before starting uvicorn —
watch the deploy logs for the migration output, then confirm `https://<backend-url>/api/v1/health`
returns 200.

## 4. Add the frontend service

New service → this repo → root directory `frontend/`. Set:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | the backend service's Railway-assigned public URL (`https://<backend>.up.railway.app`) |

This **must** be set before the first build — Next.js bakes `NEXT_PUBLIC_*` vars in at build
time, not read at runtime. If you set it after an initial build, trigger a redeploy.

Deploy, then confirm the frontend loads at its Railway URL and hits the backend without CORS
errors (there will be CORS errors until step 5 — that's expected).

## 5. Close the loop: point the backend at the real frontend URL

Now that both URLs exist, go back to the backend service's variables and update:

- `CORS_ORIGINS` → the frontend's actual Railway URL
- `FRONTEND_BASE_URL` → same

Redeploy the backend. This is the one unavoidable chicken-and-egg step — the frontend's URL
isn't known until step 4 runs once.

## 6. Verify Brevo sending

Brevo won't deliver mail from an unverified sender. In your Brevo dashboard, verify the
single sender or domain matching `BREVO_SENDER_EMAIL` before relying on real invite emails —
until then, sends will fail loudly (`BrevoEmailSender` raises `EmailSendError` on a non-2xx
response rather than swallowing it).

## 7. Sign up and invite your colleague

1. Visit the frontend URL, sign up — this account becomes the company's **Owner**.
2. Go to `/team` → **Invite teammate** → enter their name, email, and role.
3. They receive a real email via Brevo this time (locally this only ever logged to the
   console) with a link to `/accept-invite?token=...` where they set a password and land
   logged in, seeing the same shared projects and candidates — company is the tenant
   boundary, not the individual user, so no further setup is needed for shared data access.

## If something doesn't come up cleanly

This is the one phase whose final verification happens outside local Docker Compose. Check,
in order: Railway deploy logs (migration failures show up here first), the backend's
`/api/v1/health` endpoint, browser devtools network tab for CORS/401s (usually means step 5
wasn't redeployed yet), and the Postgres plugin's connection details against what's actually
set in `DATABASE_URL`/`AUTH_DATABASE_URL`/`MIGRATION_DATABASE_URL`.
