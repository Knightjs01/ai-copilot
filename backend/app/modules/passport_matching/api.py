import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.dependencies import (
    CurrentUser,
    get_email_sender,
    get_tenant_db,
    require_mfa_enrolled,
    require_permission,
)
from app.modules.auth.email import EmailSender
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.candidate_auth.dependencies import require_candidate_mfa_enrolled
from app.modules.candidate_auth.models import CandidateUser
from app.modules.passport_matching.dependencies import get_passport_matching_llm_client
from app.modules.passport_matching.llm_client import PassportMatchingLLMClient
from app.modules.passport_matching.schemas import (
    BatchMatchRequest,
    BoardFilters,
    CandidateSearchResult,
    PassportJobMatchRead,
    SearchQueryRequest,
    TalentPoolMatchResult,
    TalentPoolOpportunity,
)
from app.modules.passport_matching.service import PassportMatchingService

router = APIRouter(prefix="/matches", tags=["passport-matching"])


# Registered before /{shadow_job_id} -- a literal path segment must out-rank a path-param route
# registered after it, or FastAPI/Starlette greedily matches this as a (invalid) job UUID.
@router.get("/my-talent-pool-opportunities", response_model=list[TalentPoolOpportunity])
async def list_my_talent_pool_opportunities(
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> list[TalentPoolOpportunity]:
    return await PassportMatchingService(session).list_talent_pool_opportunities(
        candidate=candidate
    )


@router.get("/{shadow_job_id}", response_model=PassportJobMatchRead)
async def get_match(
    shadow_job_id: uuid.UUID,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
    llm_client: PassportMatchingLLMClient = Depends(get_passport_matching_llm_client),
) -> PassportJobMatchRead:
    return await PassportMatchingService(session, llm_client=llm_client).get_or_compute_match(
        candidate=candidate, shadow_job_id=shadow_job_id
    )


@router.post("/batch", response_model=list[PassportJobMatchRead])
async def batch_get_matches(
    body: BatchMatchRequest,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
    llm_client: PassportMatchingLLMClient = Depends(get_passport_matching_llm_client),
) -> list[PassportJobMatchRead]:
    return await PassportMatchingService(
        session, llm_client=llm_client
    ).batch_get_or_compute_matches(candidate=candidate, shadow_job_ids=body.shadow_job_ids)


@router.post("/search", response_model=BoardFilters)
async def search_jobs(
    body: SearchQueryRequest,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
    llm_client: PassportMatchingLLMClient = Depends(get_passport_matching_llm_client),
) -> BoardFilters:
    return await PassportMatchingService(session, llm_client=llm_client).parse_search_query(
        query=body.query
    )


# --- Company side (single applicant, already applied) -------------------------------------------


@router.get("/mine/{job_id}/applicants/{application_id}", response_model=PassportJobMatchRead)
async def get_applicant_match(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
    llm_client: PassportMatchingLLMClient = Depends(get_passport_matching_llm_client),
) -> PassportJobMatchRead:
    return await PassportMatchingService(
        session, llm_client=llm_client
    ).get_or_compute_match_for_applicant(actor=actor, job_id=job_id, application_id=application_id)


# --- Company side (candidate search) ------------------------------------------------------------


@router.get("/mine/{job_id}/candidates", response_model=list[CandidateSearchResult])
async def search_candidates(
    job_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_CANDIDATES_SEARCH)),
    session: AsyncSession = Depends(get_tenant_db),
    llm_client: PassportMatchingLLMClient = Depends(get_passport_matching_llm_client),
) -> list[CandidateSearchResult]:
    return await PassportMatchingService(session, llm_client=llm_client).search_candidates_for_job(
        actor=actor, job_id=job_id
    )


@router.get("/mine/{job_id}/talent-pool", response_model=list[TalentPoolMatchResult])
async def search_talent_pool(
    job_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.TALENT_POOL_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
    llm_client: PassportMatchingLLMClient = Depends(get_passport_matching_llm_client),
    email_sender: EmailSender = Depends(get_email_sender),
) -> list[TalentPoolMatchResult]:
    return await PassportMatchingService(
        session, llm_client=llm_client, email_sender=email_sender
    ).search_talent_pool_for_job(actor=actor, job_id=job_id)
