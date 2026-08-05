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

Every tenant (company) gets an isolated workspace. Every query against tenant-scoped tables must filter by company — no data leaks across tenants. This rule isn't implemented yet (Phase 1); it's called out here so it's never forgotten once real data models land.

## Running Locally

**Prerequisites**: Docker Desktop, or (for native dev) Python 3.12 + Poetry, and Node.js 20 + pnpm.

### Via Docker Compose (recommended)

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
```

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
| 1 | Foundation module — Companies, Users, RBAC, JWT auth (login/refresh/MFA/email verification/password reset), tenant isolation | Next |
| 2+ | Hiring workflow modules — projects, blueprints, candidates, privacy gateway, interviews, scorecards, decision support, ATS integrations, analytics | Planned |

Each future phase gets its own module, its own migration(s), its own tests, and its own commit — see `backend/app/modules/__init__.py` for the module contract.
