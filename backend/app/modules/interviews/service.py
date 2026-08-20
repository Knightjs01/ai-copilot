import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import AuditService
from app.modules.auth.models import User
from app.modules.candidate_auth.models import CandidateUser
from app.modules.companies.models import Company
from app.modules.interviews.exceptions import (
    ApplicationNotFoundError,
    InterviewNotFoundError,
    InvalidScheduleTimeError,
)
from app.modules.interviews.models import Interview
from app.modules.interviews.repository import InterviewRepository
from app.modules.interviews.schemas import (
    CandidateInterviewSummary,
    InterviewCreate,
    InterviewRead,
    InterviewUpdate,
)
from app.modules.shadow_jobs.models import ShadowApplication
from app.modules.shadow_jobs.repository import ShadowApplicationRepository, ShadowJobRepository


class InterviewService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._interviews = InterviewRepository(session)
        self._applications = ShadowApplicationRepository(session)
        self._jobs = ShadowJobRepository(session)
        self._audit = AuditService(session)

    # --- Company side ------------------------------------------------------------------------

    async def schedule(
        self, *, actor: User, job_id: uuid.UUID, application_id: uuid.UUID, data: InterviewCreate
    ) -> InterviewRead:
        application = await self._get_company_application(
            company_id=actor.company_id, job_id=job_id, application_id=application_id
        )
        if data.scheduled_at <= datetime.now(timezone.utc):
            raise InvalidScheduleTimeError()

        interview = await self._interviews.create(
            shadow_application_id=application.id,
            company_id=actor.company_id,
            candidate_user_id=application.candidate_user_id,
            scheduled_at=data.scheduled_at,
            location=data.location,
            meeting_link=data.meeting_link,
            scheduled_by_user_id=actor.id,
        )
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="interview.scheduled",
            target_type="shadow_application",
            target_id=application.id,
            extra_data={"interview_id": str(interview.id)},
        )
        return self._to_read(interview)

    async def update(
        self,
        *,
        actor: User,
        job_id: uuid.UUID,
        application_id: uuid.UUID,
        interview_id: uuid.UUID,
        data: InterviewUpdate,
    ) -> InterviewRead:
        interview = await self._get_company_interview(
            company_id=actor.company_id,
            job_id=job_id,
            application_id=application_id,
            interview_id=interview_id,
        )
        time_changed = data.scheduled_at is not None and data.scheduled_at != interview.scheduled_at
        if data.scheduled_at is not None:
            if data.scheduled_at <= datetime.now(timezone.utc):
                raise InvalidScheduleTimeError()
            interview.scheduled_at = data.scheduled_at
        if "location" in data.model_fields_set:
            interview.location = data.location
        if "meeting_link" in data.model_fields_set:
            interview.meeting_link = data.meeting_link
        await self._session.flush()

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="interview.rescheduled" if time_changed else "interview.updated",
            target_type="shadow_application",
            target_id=interview.shadow_application_id,
            extra_data={"interview_id": str(interview.id)},
        )
        return self._to_read(interview)

    async def cancel(
        self, *, actor: User, job_id: uuid.UUID, application_id: uuid.UUID, interview_id: uuid.UUID
    ) -> InterviewRead:
        interview = await self._get_company_interview(
            company_id=actor.company_id,
            job_id=job_id,
            application_id=application_id,
            interview_id=interview_id,
        )
        interview.status = "cancelled"
        await self._session.flush()
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="interview.cancelled",
            target_type="shadow_application",
            target_id=interview.shadow_application_id,
            extra_data={"interview_id": str(interview.id)},
        )
        return self._to_read(interview)

    async def complete(
        self, *, actor: User, job_id: uuid.UUID, application_id: uuid.UUID, interview_id: uuid.UUID
    ) -> InterviewRead:
        interview = await self._get_company_interview(
            company_id=actor.company_id,
            job_id=job_id,
            application_id=application_id,
            interview_id=interview_id,
        )
        interview.status = "completed"
        await self._session.flush()
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="interview.completed",
            target_type="shadow_application",
            target_id=interview.shadow_application_id,
            extra_data={"interview_id": str(interview.id)},
        )
        return self._to_read(interview)

    async def list_for_company(
        self, *, actor: User, job_id: uuid.UUID, application_id: uuid.UUID
    ) -> list[InterviewRead]:
        application = await self._get_company_application(
            company_id=actor.company_id, job_id=job_id, application_id=application_id
        )
        interviews = await self._interviews.list_by_application_id(application.id)
        return [self._to_read(i) for i in interviews]

    # --- Candidate side ------------------------------------------------------------------------

    async def get_for_candidate(
        self, *, candidate: CandidateUser, interview_id: uuid.UUID
    ) -> InterviewRead:
        """Symmetric to _get_company_interview's ownership check, filtered on candidate_user_id
        instead of company_id/job_id -- used by the co-pilot's interview-prep action so a
        cross-candidate interview_id fails the normal way everything else in this codebase fails
        on ownership mismatch (404), not a leaked result or a silently swallowed nudge."""
        interview = await self._interviews.get_by_id(interview_id)
        if interview is None or interview.candidate_user_id != candidate.id:
            raise InterviewNotFoundError()
        return self._to_read(interview)

    async def list_for_candidate(
        self, *, candidate: CandidateUser
    ) -> list[CandidateInterviewSummary]:
        interviews = await self._interviews.list_by_candidate_user_id(candidate.id)
        if not interviews:
            return []

        summaries: list[CandidateInterviewSummary] = []
        for interview in interviews:
            application = await self._applications.get_by_id(interview.shadow_application_id)
            if application is None:
                continue
            job = await self._jobs.get_by_id(application.shadow_job_id)
            company = await self._session.get(Company, interview.company_id)
            summaries.append(
                CandidateInterviewSummary(
                    id=interview.id,
                    application_id=application.id,
                    scheduled_at=interview.scheduled_at,
                    location=interview.location,
                    meeting_link=interview.meeting_link,
                    status=interview.status,  # type: ignore[arg-type]
                    created_at=interview.created_at,
                    job_title=job.title if job else "Unknown role",
                    company_name=company.name if company else "Unknown company",
                    callsign=application.callsign,
                )
            )
        return summaries

    # --- Shared helpers ------------------------------------------------------------------------

    async def _get_company_application(
        self, *, company_id: uuid.UUID, job_id: uuid.UUID, application_id: uuid.UUID
    ) -> ShadowApplication:
        job = await self._jobs.get_by_id(job_id)
        if job is None or job.company_id != company_id or job.deleted_at is not None:
            raise ApplicationNotFoundError()
        application = await self._applications.get_by_id(application_id)
        if application is None or application.shadow_job_id != job_id:
            raise ApplicationNotFoundError()
        return application

    async def _get_company_interview(
        self,
        *,
        company_id: uuid.UUID,
        job_id: uuid.UUID,
        application_id: uuid.UUID,
        interview_id: uuid.UUID,
    ) -> Interview:
        application = await self._get_company_application(
            company_id=company_id, job_id=job_id, application_id=application_id
        )
        interview = await self._interviews.get_by_id(interview_id)
        if interview is None or interview.shadow_application_id != application.id:
            raise InterviewNotFoundError()
        return interview

    def _to_read(self, interview: Interview) -> InterviewRead:
        return InterviewRead(
            id=interview.id,
            application_id=interview.shadow_application_id,
            scheduled_at=interview.scheduled_at,
            location=interview.location,
            meeting_link=interview.meeting_link,
            status=interview.status,  # type: ignore[arg-type]
            created_at=interview.created_at,
        )
