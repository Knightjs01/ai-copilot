from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.dependencies import (
    CurrentUser,
    get_tenant_db,
    require_mfa_enrolled,
    require_permission,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.candidate_activity.schemas import (
    AiRecommendation,
    RediscoveryCandidate,
    TimelineEntry,
)
from app.modules.candidate_activity.service import CandidateActivityService
from app.modules.passport_matching.dependencies import get_passport_matching_llm_client
from app.modules.passport_matching.llm_client import PassportMatchingLLMClient

router = APIRouter(prefix="/candidate-activity", tags=["candidate-activity"])


@router.get(
    "/mine/candidates/{callsign}/timeline",
    response_model=list[TimelineEntry],
)
async def get_candidate_timeline(
    callsign: str,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_CANDIDATES_SEARCH)),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[TimelineEntry]:
    return await CandidateActivityService(session).list_candidate_timeline(
        actor=actor, callsign=callsign
    )


@router.get("/mine/recent", response_model=list[TimelineEntry])
async def get_recent_activity(
    limit: int = Query(default=15, ge=1, le=50),
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_CANDIDATES_SEARCH)),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[TimelineEntry]:
    return await CandidateActivityService(session).list_recent_company_activity(
        actor=actor, limit=limit
    )


@router.get("/mine/rediscovery", response_model=list[RediscoveryCandidate])
async def get_rediscovery_candidates(
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_CANDIDATES_SEARCH)),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[RediscoveryCandidate]:
    return await CandidateActivityService(session).list_rediscovery_candidates(actor=actor)


@router.get("/mine/recommendation", response_model=AiRecommendation | None)
async def get_ai_recommendation(
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_CANDIDATES_SEARCH)),
    session: AsyncSession = Depends(get_tenant_db),
    llm_client: PassportMatchingLLMClient = Depends(get_passport_matching_llm_client),
) -> AiRecommendation | None:
    return await CandidateActivityService(session, llm_client=llm_client).get_ai_recommendation(
        actor=actor
    )
