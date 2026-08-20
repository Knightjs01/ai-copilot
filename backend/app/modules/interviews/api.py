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
from app.modules.interviews.schemas import (
    CandidateInterviewSummary,
    InterviewCreate,
    InterviewRead,
    InterviewUpdate,
)
from app.modules.interviews.service import InterviewService

router = APIRouter(prefix="/interviews", tags=["interviews"])


# --- Candidate side ----------------------------------------------------------------------------


@router.get("", response_model=list[CandidateInterviewSummary])
async def list_my_interviews(
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> list[CandidateInterviewSummary]:
    return await InterviewService(session).list_for_candidate(candidate=candidate)


# --- Company side --------------------------------------------------------------------------


@router.get("/mine/{job_id}/applicants/{application_id}", response_model=list[InterviewRead])
async def list_applicant_interviews(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.INTERVIEWS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[InterviewRead]:
    return await InterviewService(session).list_for_company(
        actor=actor, job_id=job_id, application_id=application_id
    )


@router.post(
    "/mine/{job_id}/applicants/{application_id}",
    response_model=InterviewRead,
    status_code=status.HTTP_201_CREATED,
)
async def schedule_applicant_interview(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    body: InterviewCreate,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.INTERVIEWS_SCHEDULE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> InterviewRead:
    return await InterviewService(session).schedule(
        actor=actor, job_id=job_id, application_id=application_id, data=body
    )


@router.patch(
    "/mine/{job_id}/applicants/{application_id}/{interview_id}", response_model=InterviewRead
)
async def update_applicant_interview(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    interview_id: uuid.UUID,
    body: InterviewUpdate,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.INTERVIEWS_SCHEDULE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> InterviewRead:
    return await InterviewService(session).update(
        actor=actor,
        job_id=job_id,
        application_id=application_id,
        interview_id=interview_id,
        data=body,
    )


@router.post(
    "/mine/{job_id}/applicants/{application_id}/{interview_id}/cancel",
    response_model=InterviewRead,
)
async def cancel_applicant_interview(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    interview_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.INTERVIEWS_SCHEDULE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> InterviewRead:
    return await InterviewService(session).cancel(
        actor=actor, job_id=job_id, application_id=application_id, interview_id=interview_id
    )


@router.post(
    "/mine/{job_id}/applicants/{application_id}/{interview_id}/complete",
    response_model=InterviewRead,
)
async def complete_applicant_interview(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    interview_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.INTERVIEWS_SCHEDULE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> InterviewRead:
    return await InterviewService(session).complete(
        actor=actor, job_id=job_id, application_id=application_id, interview_id=interview_id
    )
