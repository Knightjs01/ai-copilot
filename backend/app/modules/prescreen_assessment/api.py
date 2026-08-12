import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user_model,
    get_tenant_db,
    require_mfa_enrolled,
    require_permission,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.prescreen_assessment.dependencies import get_prescreen_assessment_llm_client
from app.modules.prescreen_assessment.llm_client import PrescreenAssessmentLLMClient
from app.modules.prescreen_assessment.schemas import PrescreenAssessmentRead
from app.modules.prescreen_assessment.service import PrescreenAssessmentService

router = APIRouter(
    prefix="/candidates",
    tags=["prescreen-assessment"],
    dependencies=[Depends(require_mfa_enrolled)],
)


@router.post("/{candidate_id}/prescreen-assessment", response_model=PrescreenAssessmentRead)
async def generate_prescreen_assessment(
    candidate_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.CANDIDATES_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
    llm_client: PrescreenAssessmentLLMClient = Depends(get_prescreen_assessment_llm_client),
) -> PrescreenAssessmentRead:
    assessment = await PrescreenAssessmentService(
        session, llm_client=llm_client
    ).generate_assessment(actor=actor, candidate_id=candidate_id)
    return PrescreenAssessmentRead.model_validate(assessment)


@router.get("/{candidate_id}/prescreen-assessment", response_model=PrescreenAssessmentRead)
async def get_prescreen_assessment(
    candidate_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.CANDIDATES_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> PrescreenAssessmentRead:
    assessment = await PrescreenAssessmentService(session).get_assessment(
        company_id=actor.company_id, candidate_id=candidate_id
    )
    return PrescreenAssessmentRead.model_validate(assessment)


@router.post("/{candidate_id}/prescreen-assessment/handoff", response_model=PrescreenAssessmentRead)
async def generate_handoff_recommendations(
    candidate_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.CANDIDATES_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
    llm_client: PrescreenAssessmentLLMClient = Depends(get_prescreen_assessment_llm_client),
) -> PrescreenAssessmentRead:
    assessment = await PrescreenAssessmentService(
        session, llm_client=llm_client
    ).generate_handoff_recommendations(actor=actor, candidate_id=candidate_id)
    return PrescreenAssessmentRead.model_validate(assessment)
