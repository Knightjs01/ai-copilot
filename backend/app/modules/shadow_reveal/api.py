import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user_model,
    get_tenant_db,
    require_permission,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.candidate_auth.dependencies import get_current_candidate
from app.modules.candidate_auth.models import CandidateUser
from app.modules.shadow_reveal.schemas import (
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
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> RevealRequestRead:
    return await ShadowRevealService(session).request_reveal(
        actor=actor, job_id=job_id, application_id=application_id, body=body
    )


@router.get("/mine/{job_id}/applicants/{application_id}", response_model=RevealedIdentity)
async def get_revealed_identity(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> RevealedIdentity:
    return await ShadowRevealService(session).get_revealed_identity(
        company_id=actor.company_id, job_id=job_id, application_id=application_id
    )


# --- Candidate side ----------------------------------------------------------------------------


@router.get("/applications/me/{application_id}", response_model=CandidateRevealRequestRead)
async def get_my_reveal_request(
    application_id: uuid.UUID,
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> CandidateRevealRequestRead:
    return await ShadowRevealService(session).get_my_reveal_request(
        candidate=candidate, application_id=application_id
    )


@router.post("/applications/me/{application_id}/respond", response_model=CandidateRevealRequestRead)
async def respond_to_reveal_request(
    application_id: uuid.UUID,
    body: RevealDecision,
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> CandidateRevealRequestRead:
    return await ShadowRevealService(session).respond_to_reveal_request(
        candidate=candidate, application_id=application_id, body=body
    )
