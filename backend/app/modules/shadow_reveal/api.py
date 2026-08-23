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
    require_step_up,
)
from app.modules.auth.email import EmailSender
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.candidate_auth.dependencies import require_candidate_mfa_enrolled
from app.modules.candidate_auth.models import CandidateUser
from app.modules.shadow_reveal.schemas import (
    CandidateRevealHistoryItem,
    CandidateRevealRequestRead,
    RevealDecision,
    RevealedIdentity,
    RevealRequestCreate,
    RevealRequestRead,
)
from app.modules.shadow_reveal.service import ShadowRevealService

router = APIRouter(prefix="/shadow-reveal", tags=["shadow-reveal"])


# --- Company side ----------------------------------------------------------------------------


@router.post(
    "/mine/{job_id}/applicants/{application_id}/request",
    response_model=RevealRequestRead,
    status_code=status.HTTP_201_CREATED,
)
async def request_reveal(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    body: RevealRequestCreate,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> RevealRequestRead:
    return await ShadowRevealService(session, email_sender=email_sender).request_reveal(
        actor=actor, job_id=job_id, application_id=application_id, body=body
    )


@router.get("/mine/{job_id}/applicants/{application_id}", response_model=RevealedIdentity)
async def get_revealed_identity(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    actor: User = Depends(require_step_up),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> RevealedIdentity:
    return await ShadowRevealService(session).get_revealed_identity(
        company_id=actor.company_id,
        job_id=job_id,
        application_id=application_id,
        actor_user_id=actor.id,
    )


# --- Candidate side ----------------------------------------------------------------------------


@router.get("/my-history", response_model=list[CandidateRevealHistoryItem])
async def list_my_reveal_history(
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> list[CandidateRevealHistoryItem]:
    return await ShadowRevealService(session).list_my_reveal_history(candidate=candidate)


@router.get("/applications/me/{application_id}", response_model=CandidateRevealRequestRead)
async def get_my_reveal_request(
    application_id: uuid.UUID,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> CandidateRevealRequestRead:
    return await ShadowRevealService(session).get_my_reveal_request(
        candidate=candidate, application_id=application_id
    )


@router.post("/applications/me/{application_id}/respond", response_model=CandidateRevealRequestRead)
async def respond_to_reveal_request(
    application_id: uuid.UUID,
    body: RevealDecision,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> CandidateRevealRequestRead:
    return await ShadowRevealService(session, email_sender=email_sender).respond_to_reveal_request(
        candidate=candidate, application_id=application_id, body=body
    )
