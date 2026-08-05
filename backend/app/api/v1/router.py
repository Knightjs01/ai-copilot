from fastapi import APIRouter

from app.api.v1 import health
from app.modules.auth.api import router as auth_router
from app.modules.candidates.api import router as candidates_router
from app.modules.companies.api import router as companies_router
from app.modules.hiring_blueprint.api import router as hiring_blueprint_router
from app.modules.hiring_manager_alignment.api import router as hiring_manager_alignment_router
from app.modules.intelligence.api import router as intelligence_router
from app.modules.prescreen_assessment.api import router as prescreen_assessment_router
from app.modules.privacy_gateway.api import router as privacy_gateway_router
from app.modules.projects.api import router as projects_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth_router)
api_router.include_router(companies_router)
api_router.include_router(projects_router)
api_router.include_router(candidates_router)
api_router.include_router(privacy_gateway_router)
api_router.include_router(intelligence_router)
api_router.include_router(hiring_blueprint_router)
api_router.include_router(hiring_manager_alignment_router)
api_router.include_router(prescreen_assessment_router)

# Everything past pre-screen (interview loops, scorecards, offer, decision) is handled in the
# company's ATS (Greenhouse), not this platform — see README Roadmap.
