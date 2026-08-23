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
from app.modules.interviews.dependencies import get_interview_scorecard_llm_client
from app.modules.interviews.llm_client import InterviewScorecardLLMClient
from app.modules.interviews.schemas import (
    CandidateInterviewSummary,
    CompanyInterviewSummary,
    InterviewCreate,
    InterviewRead,
    InterviewScorecardDraft,
    InterviewScorecardGenerateRequest,
    InterviewScorecardRead,
    InterviewScorecardSave,
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


@router.get("/mine", response_model=list[CompanyInterviewSummary])
async def list_company_interviews(
    actor: User = Depends(require_mfa_enrolled),
    current_user: CurrentUser = Depends(require_permission(Permissions.INTERVIEWS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[CompanyInterviewSummary]:
    return await InterviewService(session).list_for_company_wide(
        actor=actor, permissions=current_user.permissions
    )


@router.get("/mine/{job_id}/applicants/{application_id}", response_model=list[InterviewRead])
async def list_applicant_interviews(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    current_user: CurrentUser = Depends(require_permission(Permissions.INTERVIEWS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[InterviewRead]:
    return await InterviewService(session).list_for_company(
        actor=actor,
        permissions=current_user.permissions,
        job_id=job_id,
        application_id=application_id,
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
    email_sender: EmailSender = Depends(get_email_sender),
) -> InterviewRead:
    return await InterviewService(session, email_sender=email_sender).schedule(
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


@router.post(
    "/mine/{job_id}/applicants/{application_id}/{interview_id}/scorecard/generate",
    response_model=InterviewScorecardDraft,
)
async def generate_applicant_interview_scorecard(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    interview_id: uuid.UUID,
    body: InterviewScorecardGenerateRequest,
    actor: User = Depends(require_mfa_enrolled),
    current_user: CurrentUser = Depends(require_permission(Permissions.INTERVIEWS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
    scorecard_llm_client: InterviewScorecardLLMClient = Depends(get_interview_scorecard_llm_client),
) -> InterviewScorecardDraft:
    return await InterviewService(
        session, scorecard_llm_client=scorecard_llm_client
    ).generate_scorecard_draft(
        actor=actor,
        permissions=current_user.permissions,
        job_id=job_id,
        application_id=application_id,
        interview_id=interview_id,
        notes=body.notes,
    )


@router.put(
    "/mine/{job_id}/applicants/{application_id}/{interview_id}/scorecard",
    response_model=InterviewScorecardRead,
)
async def save_applicant_interview_scorecard(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    interview_id: uuid.UUID,
    body: InterviewScorecardSave,
    actor: User = Depends(require_mfa_enrolled),
    current_user: CurrentUser = Depends(require_permission(Permissions.INTERVIEWS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> InterviewScorecardRead:
    return await InterviewService(session).save_scorecard(
        actor=actor,
        permissions=current_user.permissions,
        job_id=job_id,
        application_id=application_id,
        interview_id=interview_id,
        notes=body.notes,
        competency_scores=body.competency_scores,
        overall_recommendation=body.overall_recommendation,
    )


@router.get(
    "/mine/{job_id}/applicants/{application_id}/{interview_id}/scorecards",
    response_model=list[InterviewScorecardRead],
)
async def list_applicant_interview_scorecards(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    interview_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    current_user: CurrentUser = Depends(require_permission(Permissions.INTERVIEWS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[InterviewScorecardRead]:
    return await InterviewService(session).list_scorecards_for_interview(
        actor=actor,
        permissions=current_user.permissions,
        job_id=job_id,
        application_id=application_id,
        interview_id=interview_id,
    )
