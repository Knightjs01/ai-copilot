# AI Interview Copilot

A secure, enterprise-grade, multi-tenant AI hiring platform — an operating system for recruitment, from role creation through hiring decisions, built with privacy-first AI and evidence-based assessments.

This repo is being built **iteratively, phase by phase**. Each phase is designed, implemented, tested, and committed before the next one starts. See [Roadmap](#roadmap) below for where things stand.

## Tech Stack

**Backend** — Python, FastAPI, SQLAlchemy (async), PostgreSQL, Alembic, Pydantic, REST + WebSockets
**Frontend** — Next.js (App Router), TypeScript, TailwindCSS, shadcn/ui, Framer Motion, React Query, TanStack Table, Recharts
**Infra** — Docker, Docker Compose (local dev), Railway (hosting), GitHub Actions (CI)

## Architecture

Clean architecture, layered top to bottom:

```
Presentation (API routers) → Service (use cases) → Domain (business rules) → Repository (persistence) → Database
```

Every feature lives in its own module under `backend/app/modules/<name>/`, each with its own `api.py`, `service.py`, `domain.py`, `repository.py`, and `models.py`. Modules don't reach into each other's repositories directly — cross-module calls go through the other module's service layer. See `backend/app/modules/__init__.py` for the full layer contract.

Every tenant (company) gets an isolated workspace. Every query against tenant-scoped tables must filter by company — no data leaks across tenants. This is enforced with Postgres row-level security (not just application-level filtering) as of Phase 1: see `backend/alembic/versions/0001_phase1_foundation.py` for the RLS policy and the three-role connection setup, and `backend/app/modules/auth/dependencies.py` for `get_tenant_db`.

## Running Locally

**Prerequisites**: Docker Desktop, or (for native dev) Python 3.12 + Poetry, and Node.js 20 + pnpm.

### Via Docker Compose (recommended)

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
```

`backend/.env.example` documents (as inline comments) the `python -c ...` one-liners to generate `SECRET_KEY`, `ENCRYPTION_KEY`, `APP_DB_PASSWORD`, and `AUTH_DB_PASSWORD` — fill those in (and the matching passwords embedded in `DATABASE_URL`/`AUTH_DATABASE_URL`) before starting the stack for the first time. See that file's comments for why there are three separate DB roles.

- Backend: http://localhost:8000/api/docs
- Frontend: http://localhost:3000

### Natively

```bash
# Backend
cd backend
cp .env.example .env
poetry install
poetry run uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
cp .env.example .env
pnpm install
pnpm dev
```

### Tests

```bash
cd backend
poetry run pytest
```

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 0 | Foundation scaffold — repo structure, clean-architecture skeleton, Docker Compose, CI, health check | ✅ Done |
| 1 | Foundation module — Companies, Users, RBAC, JWT auth (login/refresh/MFA/email verification/password reset), Postgres RLS tenant isolation | ✅ Done |
| 2 | Projects module — create/list/view/update/archive hiring projects (workflow Stage 1) | ✅ Done |
| 3 | Candidates module — candidate CRUD + resume upload/download attached to a project (workflow Stage 4) | ✅ Done |
| 4+ | Remaining hiring workflow modules — AI hiring blueprint, stakeholder alignment, privacy gateway, interviews, scorecards, decision support, ATS integrations, analytics | Next |

Each future phase gets its own module, its own migration(s), its own tests, and its own commit — see `backend/app/modules/__init__.py` for the module contract.
