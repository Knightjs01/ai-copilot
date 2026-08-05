from fastapi import APIRouter

from app.api.v1 import health
from app.modules.auth.api import router as auth_router
from app.modules.companies.api import router as companies_router
from app.modules.projects.api import router as projects_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth_router)
api_router.include_router(companies_router)
api_router.include_router(projects_router)

# Future modules (candidates, interviews, ...) register their routers here.
