# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What This Is

AI Interview Copilot — a commercially deployable, multi-tenant SaaS platform for AI-assisted hiring (competing with Metaview, BrightHire, Screenloop, Ashby). Not a prototype. Every decision should prioritize scalability, security, maintainability, and enterprise readiness over speed of typing.

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy (async), PostgreSQL, Alembic, Pydantic, REST + WebSockets where needed
- **Frontend**: Next.js (App Router), TypeScript, TailwindCSS, shadcn/ui, Framer Motion, React Query, TanStack Table, Recharts
- **Infra**: Docker/Docker Compose, Railway hosting, GitHub Actions CI, Redis
- **Package managers**: Poetry (backend), pnpm (frontend)

## Architecture Rules

- Clean architecture, strictly layered: Presentation (API routers) → Service → Domain → Repository → Database. No business logic in routers.
- Every feature is its own module under `backend/app/modules/<name>/`, with `api.py`, `schemas.py`, `service.py`, `domain.py`, `repository.py`, `models.py`. Modules call each other's *service* layer only — never reach into another module's repository or ORM models directly.
- No duplicated logic — extract to shared services/utilities instead.
- Every DB table needs: foreign keys, indexes where queried, soft deletes, `created_at`/`updated_at`.

## Multi-Tenancy (non-negotiable)

Every company is an isolated workspace. **Every query against a tenant-scoped table must filter by company/tenant ID.** No cross-tenant data access, ever — this is a security requirement, not a nice-to-have. When adding a new tenant-scoped table or query, verify the tenant filter is present before considering the work done.

## AI Integration Rule

Never send raw CVs or other uploaded PII directly to an LLM. The pipeline is always: extract structured data → strip PII → build an anonymized professional profile → delete the original upload → only then send the anonymized profile to the AI. The AI must never receive name, email, phone, address, DOB, LinkedIn URL, or photograph.

## Security Baseline

OWASP Top 10, GDPR, privacy-by-design, least privilege, data minimization. Every user-facing input is validated at the boundary. Secrets come from environment variables, never hardcoded. Auth uses JWT + refresh tokens in secure HTTP-only cookies, RBAC, and MFA — implemented once, in the auth module, not re-implemented per module.

## Development Process

Work module by module, not in one pass. For each module: design → schema → backend → API → frontend → tests → verify → refactor → commit. Don't start the next module until the current one is committed and working. See `README.md` for the current phase and roadmap.

## Code Quality

Typed, validated, tested. Follow SOLID/DRY/KISS. Every function that can fail returns a proper error, not a silent default. No commented-out code, no dead code, no TODO stubs left half-finished — either build it or don't start it.
