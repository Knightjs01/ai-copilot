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
from app.modules.shadow_introduction.schemas import (
    CandidateIntroductionRequestRead,
    IntroductionDecision,
    IntroductionRequestCreate,
    IntroductionRequestRead,
)
from app.modules.shadow_introduction.service import IntroductionService

router = APIRouter(prefix="/introductions", tags=["shadow-introductions"])


# --- Company side --------------------------------------------------------------------------


@router.post(
    "/mine/{job_id}/candidates/{callsign}/request",
    response_model=IntroductionRequestRead,
    status_code=status.HTTP_201_CREATED,
)
async def request_introduction(
    job_id: uuid.UUID,
    callsign: str,
    body: IntroductionRequestCreate,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_INTRODUCTION_REQUEST)),
    session: AsyncSession = Depends(get_tenant_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> IntroductionRequestRead:
    return await IntroductionService(session, email_sender=email_sender).request_introduction(
        actor=actor, job_id=job_id, callsign=callsign, body=body
    )


@router.get("/mine/{job_id}", response_model=list[IntroductionRequestRead])
async def list_company_introduction_requests(
    job_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_INTRODUCTION_REQUEST)),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[IntroductionRequestRead]:
    return await IntroductionService(session).list_company_introduction_requests(
        actor=actor, job_id=job_id
    )


# --- Candidate side ------------------------------------------------------------------------


@router.get("/my-requests", response_model=list[CandidateIntroductionRequestRead])
async def list_my_introduction_requests(
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> list[CandidateIntroductionRequestRead]:
    return await IntroductionService(session).list_my_introduction_requests(candidate=candidate)


@router.post("/requests/me/{request_id}/respond", response_model=CandidateIntroductionRequestRead)
async def respond_to_introduction_request(
    request_id: uuid.UUID,
    body: IntroductionDecision,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> CandidateIntroductionRequestRead:
    return await IntroductionService(session, email_sender=email_sender).respond_to_introduction_request(
        candidate=candidate, request_id=request_id, body=body
    )
