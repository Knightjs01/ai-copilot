import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.dependencies import (
    CurrentUser,
    get_tenant_db,
    require_mfa_enrolled,
    require_permission,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.candidate_auth.dependencies import require_candidate_mfa_enrolled
from app.modules.candidate_auth.models import CandidateUser
from app.modules.messages.schemas import MessageCreate, MessageThreadRead, MessageThreadSummary
from app.modules.messages.service import MessageService

router = APIRouter(prefix="/messages", tags=["messages"])


# --- Candidate side ----------------------------------------------------------------------------


@router.get("", response_model=list[MessageThreadSummary])
async def list_my_message_threads(
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> list[MessageThreadSummary]:
    return await MessageService(session).list_threads_for_candidate(candidate=candidate)


@router.get("/{application_id}", response_model=MessageThreadRead)
async def get_my_message_thread(
    application_id: uuid.UUID,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> MessageThreadRead:
    return await MessageService(session).get_thread_for_candidate(
        candidate=candidate, application_id=application_id
    )


@router.post(
    "/{application_id}", response_model=MessageThreadRead, status_code=status.HTTP_201_CREATED
)
async def send_my_message(
    application_id: uuid.UUID,
    body: MessageCreate,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> MessageThreadRead:
    return await MessageService(session).send_as_candidate(
        candidate=candidate, application_id=application_id, body=body.body
    )


# --- Company side --------------------------------------------------------------------------


@router.get("/mine/{job_id}/applicants/{application_id}", response_model=MessageThreadRead)
async def get_applicant_message_thread(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.MESSAGES_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> MessageThreadRead:
    return await MessageService(session).get_thread_for_company(
        actor=actor, job_id=job_id, application_id=application_id
    )


@router.post(
    "/mine/{job_id}/applicants/{application_id}",
    response_model=MessageThreadRead,
    status_code=status.HTTP_201_CREATED,
)
async def send_applicant_message(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    body: MessageCreate,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.MESSAGES_SEND)),
    session: AsyncSession = Depends(get_tenant_db),
) -> MessageThreadRead:
    return await MessageService(session).send_as_company(
        actor=actor, job_id=job_id, application_id=application_id, body=body.body
    )
