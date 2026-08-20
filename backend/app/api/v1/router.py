from fastapi import APIRouter

from app.api.v1 import health
from app.modules.analytics.api import router as analytics_router
from app.modules.auth.api import router as auth_router
from app.modules.candidate_auth.api import router as candidate_auth_router
from app.modules.candidates.api import router as candidates_router
from app.modules.companies.api import public_router as companies_public_router
from app.modules.companies.api import router as companies_router
from app.modules.copilot.api import router as copilot_router
from app.modules.dashboard.api import router as dashboard_router
from app.modules.hiring_blueprint.api import router as hiring_blueprint_router
from app.modules.hiring_manager_alignment.api import router as hiring_manager_alignment_router
from app.modules.historic_vault.api import router as historic_vault_router
from app.modules.identity_vault.api import router as identity_vault_router
from app.modules.intelligence.api import router as intelligence_router
from app.modules.interview_kit.api import router as interview_kit_router
from app.modules.interviews.api import router as interviews_router
from app.modules.job_alerts.api import router as job_alerts_router
from app.modules.messages.api import router as messages_router
from app.modules.passport_matching.api import router as passport_matching_router
from app.modules.phantom_passport.api import public_router as phantom_passport_public_router
from app.modules.phantom_passport.api import router as phantom_passport_router
from app.modules.prescreen_assessment.api import router as prescreen_assessment_router
from app.modules.privacy_gateway.api import router as privacy_gateway_router
from app.modules.project_deletion.api import router as project_deletion_router
from app.modules.projects.api import router as projects_router
from app.modules.saved_shadow_jobs.api import router as saved_shadow_jobs_router
from app.modules.shadow_jobs.api import router as shadow_jobs_router
from app.modules.shadow_reveal.api import router as shadow_reveal_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth_router)
api_router.include_router(companies_router)
api_router.include_router(companies_public_router)
api_router.include_router(projects_router)
api_router.include_router(candidates_router)
api_router.include_router(privacy_gateway_router)
api_router.include_router(intelligence_router)
api_router.include_router(hiring_blueprint_router)
api_router.include_router(interview_kit_router)
api_router.include_router(hiring_manager_alignment_router)
api_router.include_router(prescreen_assessment_router)
api_router.include_router(project_deletion_router)
api_router.include_router(analytics_router)
api_router.include_router(identity_vault_router)
api_router.include_router(dashboard_router)
api_router.include_router(historic_vault_router)
api_router.include_router(candidate_auth_router)
api_router.include_router(phantom_passport_router)
api_router.include_router(shadow_jobs_router)
api_router.include_router(shadow_reveal_router)
api_router.include_router(saved_shadow_jobs_router)
api_router.include_router(passport_matching_router)
api_router.include_router(messages_router)
api_router.include_router(interviews_router)
api_router.include_router(copilot_router)
api_router.include_router(job_alerts_router)
api_router.include_router(phantom_passport_public_router)

# Everything past pre-screen (interview loops, scorecards, offer, decision) is handled in the
# company's ATS (Greenhouse), not this platform — see README Roadmap.
