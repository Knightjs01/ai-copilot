# Feature modules live here, one package per domain (auth, projects, candidates,
# interviews, scorecards, reports, integrations, admin, analytics, ...).
#
# Each module owns its own layers:
#   <module>/api.py          — FastAPI router (presentation)
#   <module>/schemas.py      — Pydantic request/response models
#   <module>/service.py      — application/use-case logic
#   <module>/domain.py       — domain entities and business rules
#   <module>/repository.py   — persistence access (SQLAlchemy)
#   <module>/models.py       — ORM models (inherit app.db.base.Base)
#
# No module reaches into another module's repository or ORM models directly —
# cross-module calls go through the other module's service layer.
