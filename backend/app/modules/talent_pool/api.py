import uuid

from fastapi import APIRouter, Depends, status
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
from app.modules.talent_pool.schemas import (
    CandidateTalentPoolRequestRead,
    TalentPoolBulkRequestCreate,
    TalentPoolBulkRequestResult,
    TalentPoolDecision,
    TalentPoolGrantRead,
    TalentPoolPoolListItem,
    TalentPoolRequestCreate,
)
from app.modules.talent_pool.service import TalentPoolService

router = APIRouter(prefix="/talent-pool", tags=["talent-pool"])


# --- Company side ------------------------------------------------------------------------------


@router.post(
    "/mine/{job_id}/applicants/{application_id}/request",
    response_model=TalentPoolGrantRead,
    status_code=status.HTTP_201_CREATED,
)
async def request_talent_pool(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    body: TalentPoolRequestCreate,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.TALENT_POOL_REQUEST)),
    session: AsyncSession = Depends(get_tenant_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> TalentPoolGrantRead:
    return await TalentPoolService(session, email_sender=email_sender).request_talent_pool(
        actor=actor, job_id=job_id, application_id=application_id, body=body
    )


@router.post("/mine/search/request-bulk", response_model=TalentPoolBulkRequestResult)
async def request_talent_pool_bulk(
    body: TalentPoolBulkRequestCreate,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.TALENT_POOL_REQUEST)),
    session: AsyncSession = Depends(get_tenant_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> TalentPoolBulkRequestResult:
    return await TalentPoolService(session, email_sender=email_sender).request_talent_pool_bulk(
        actor=actor, job_id=body.job_id, callsigns=body.callsigns, note=body.note
    )


@router.get("/mine", response_model=list[TalentPoolPoolListItem])
async def list_company_talent_pool(
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.TALENT_POOL_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[TalentPoolPoolListItem]:
    return await TalentPoolService(session).list_company_talent_pool(company_id=actor.company_id)


@router.get("/mine/projects/{project_id}/eligible", response_model=list[TalentPoolPoolListItem])
async def list_eligible_for_project(
    project_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.TALENT_POOL_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[TalentPoolPoolListItem]:
    return await TalentPoolService(session).list_eligible_for_project(
        actor=actor, project_id=project_id
    )


# --- Candidate side ------------------------------------------------------------------------------


@router.get("/my-requests", response_model=list[CandidateTalentPoolRequestRead])
async def list_my_talent_pool_requests(
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> list[CandidateTalentPoolRequestRead]:
    return await TalentPoolService(session).list_my_talent_pool_requests(candidate=candidate)


@router.post("/requests/me/{grant_id}/respond", response_model=CandidateTalentPoolRequestRead)
async def respond_to_talent_pool_request(
    grant_id: uuid.UUID,
    body: TalentPoolDecision,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> CandidateTalentPoolRequestRead:
    return await TalentPoolService(session).respond_to_talent_pool_request(
        candidate=candidate, grant_id=grant_id, body=body
    )


@router.post("/requests/me/{grant_id}/withdraw", response_model=CandidateTalentPoolRequestRead)
async def withdraw_talent_pool_grant(
    grant_id: uuid.UUID,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> CandidateTalentPoolRequestRead:
    return await TalentPoolService(session).withdraw_talent_pool_grant(
        candidate=candidate, grant_id=grant_id
    )
