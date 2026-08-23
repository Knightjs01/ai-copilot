import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.audit.service import AuditService
from app.modules.auth.email import EmailSender, build_interview_scheduled_email
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.auth.service.user_service import UserService
from app.modules.candidate_auth.models import CandidateUser
from app.modules.candidate_auth.repository import CandidateUserRepository
from app.modules.companies.models import Company
from app.modules.hiring_manager_alignment.repository import HiringManagerAlignmentRepository
from app.modules.interviews.exceptions import (
    ApplicationNotFoundError,
    InterviewNotFoundError,
    InterviewScorecardGenerationError,
    InterviewScorecardNotesRequiredError,
    InvalidInterviewerError,
    InvalidScheduleTimeError,
)
from app.modules.interviews.llm_client import InterviewScorecardLLMClient, LLMRequestError
from app.modules.interviews.models import Interview, InterviewScorecard
from app.modules.interviews.repository import (
    InterviewParticipantRepository,
    InterviewRepository,
    InterviewScorecardRepository,
)
from app.modules.interviews.schemas import (
    CandidateInterviewSummary,
    CompanyInterviewSummary,
    CompetencyScore,
    InterviewCreate,
    InterviewRead,
    InterviewScorecardDraft,
    InterviewScorecardRead,
    InterviewUpdate,
)
from app.modules.privacy_gateway.redaction import redact_text
from app.modules.shadow_jobs.models import ShadowApplication, ShadowJob
from app.modules.shadow_jobs.repository import ShadowApplicationRepository, ShadowJobRepository

logger = logging.getLogger("app.interviews.service")


class InterviewService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        email_sender: EmailSender | None = None,
        scorecard_llm_client: InterviewScorecardLLMClient | None = None,
    ) -> None:
        self._session = session
        self._interviews = InterviewRepository(session)
        self._participants = InterviewParticipantRepository(session)
        self._scorecards = InterviewScorecardRepository(session)
        self._applications = ShadowApplicationRepository(session)
        self._jobs = ShadowJobRepository(session)
        self._alignments = HiringManagerAlignmentRepository(session)
        self._candidate_users = CandidateUserRepository(session)
        self._audit = AuditService(session)
        self._users = UserService(session)
        self._email_sender = email_sender
        self._scorecard_llm_client = scorecard_llm_client
        self._settings = get_settings()

    # --- Company side ------------------------------------------------------------------------

    async def schedule(
        self, *, actor: User, job_id: uuid.UUID, application_id: uuid.UUID, data: InterviewCreate
    ) -> InterviewRead:
        application = await self._get_company_application(
            company_id=actor.company_id, job_id=job_id, application_id=application_id
        )
        if data.scheduled_at <= datetime.now(timezone.utc):
            raise InvalidScheduleTimeError()
        await self._validate_interviewers(
            company_id=actor.company_id, user_ids=data.interviewer_user_ids
        )

        interview = await self._interviews.create(
            shadow_application_id=application.id,
            company_id=actor.company_id,
            candidate_user_id=application.candidate_user_id,
            scheduled_at=data.scheduled_at,
            location=data.location,
            meeting_link=data.meeting_link,
            scheduled_by_user_id=actor.id,
        )
        await self._participants.set_participants(
            interview_id=interview.id,
            company_id=actor.company_id,
            user_ids=data.interviewer_user_ids,
        )
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="interview.scheduled",
            target_type="shadow_application",
            target_id=application.id,
            extra_data={"interview_id": str(interview.id)},
        )
        await self._notify_candidate_of_scheduled_interview(actor=actor, interview=interview)
        return await self._to_read(interview)

    async def _notify_candidate_of_scheduled_interview(
        self, *, actor: User, interview: Interview
    ) -> None:
        if self._email_sender is None:
            return
        candidate = await self._candidate_users.get_by_id(interview.candidate_user_id)
        company = await self._session.get(Company, actor.company_id)
        if candidate is None or company is None:
            return
        interviews_url = f"{self._settings.frontend_base_url}/shadow/interviews"
        subject, body = build_interview_scheduled_email(
            company_name=company.name,
            scheduled_at_display=interview.scheduled_at.strftime("%A %d %B %Y, %H:%M UTC"),
            interviews_url=interviews_url,
        )
        try:
            await self._email_sender.send(to=candidate.email, subject=subject, body=body)
        except Exception:
            # A send failure must never fail the schedule request it's riding along with.
            logger.exception(
                "Failed to send interview-scheduled email to candidate %s for interview %s",
                candidate.id,
                interview.id,
            )

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
        if data.interviewer_user_ids is not None:
            await self._validate_interviewers(
                company_id=actor.company_id, user_ids=data.interviewer_user_ids
            )
            await self._participants.set_participants(
                interview_id=interview.id,
                company_id=actor.company_id,
                user_ids=data.interviewer_user_ids,
            )
        await self._session.flush()

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="interview.rescheduled" if time_changed else "interview.updated",
            target_type="shadow_application",
            target_id=interview.shadow_application_id,
            extra_data={"interview_id": str(interview.id)},
        )
        return await self._to_read(interview)

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
        return await self._to_read(interview)

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
        return await self._to_read(interview)

    async def list_for_company(
        self,
        *,
        actor: User,
        permissions: set[str],
        job_id: uuid.UUID,
        application_id: uuid.UUID,
    ) -> list[InterviewRead]:
        application = await self._get_company_application(
            company_id=actor.company_id, job_id=job_id, application_id=application_id
        )
        interviews = await self._interviews.list_by_application_id(application.id)

        # Anyone who can schedule interviews (Owner/TA Admin/Recruiter) keeps today's unscoped
        # company-wide visibility for interviews on this application. Only a viewer without that
        # permission (today: Interviewer) is scoped down to interviews they're a participant on
        # -- a new, narrower role, not a narrowing of existing behavior for anyone else.
        if Permissions.INTERVIEWS_SCHEDULE not in permissions:
            assigned_ids = set(await self._participants.list_interview_ids_for_user(actor.id))
            interviews = [i for i in interviews if i.id in assigned_ids]

        return [await self._to_read(i) for i in interviews]

    async def list_for_company_wide(
        self, *, actor: User, permissions: set[str]
    ) -> list[CompanyInterviewSummary]:
        """Company-wide Interviews nav destination -- every interview across every job for this
        tenant, same Interviewer-participant scoping as list_for_company but by company_id
        instead of one application at a time."""
        interviews = await self._interviews.list_by_company_id(actor.company_id)

        if Permissions.INTERVIEWS_SCHEDULE not in permissions:
            assigned_ids = set(await self._participants.list_interview_ids_for_user(actor.id))
            interviews = [i for i in interviews if i.id in assigned_ids]

        summaries: list[CompanyInterviewSummary] = []
        for interview in interviews:
            application = await self._applications.get_by_id(interview.shadow_application_id)
            if application is None:
                continue
            job = await self._jobs.get_by_id(application.shadow_job_id)
            interviewer_user_ids = await self._participants.list_user_ids_for_interview(
                interview.id
            )
            summaries.append(
                CompanyInterviewSummary(
                    id=interview.id,
                    application_id=application.id,
                    scheduled_at=interview.scheduled_at,
                    location=interview.location,
                    meeting_link=interview.meeting_link,
                    status=interview.status,  # type: ignore[arg-type]
                    created_at=interview.created_at,
                    interviewer_user_ids=interviewer_user_ids,
                    job_title=job.title if job else "Unknown role",
                    callsign=application.callsign,
                    project_id=job.project_id if job else None,
                    shadow_job_id=application.shadow_job_id,
                )
            )
        return summaries

    # --- Scorecards ----------------------------------------------------------------------------

    async def generate_scorecard_draft(
        self,
        *,
        actor: User,
        permissions: set[str],
        job_id: uuid.UUID,
        application_id: uuid.UUID,
        interview_id: uuid.UUID,
        notes: str,
    ) -> InterviewScorecardDraft:
        if self._scorecard_llm_client is None:
            raise ValueError("generate_scorecard_draft requires a scorecard_llm_client")
        if not notes.strip():
            raise InterviewScorecardNotesRequiredError()

        interview, application, job = await self._get_interview_for_scoring(
            actor=actor,
            permissions=permissions,
            job_id=job_id,
            application_id=application_id,
            interview_id=interview_id,
        )

        redacted_notes, _ = redact_text(
            text=notes, known_full_name=application.revealed_full_name or ""
        )

        requirements: list[str] | None = None
        if job.project_id is not None:
            alignment = await self._alignments.get_by_project_id(job.project_id)
            if alignment is not None:
                requirements = alignment.top_requirements

        try:
            extraction = await self._scorecard_llm_client.generate_scorecard(
                notes=redacted_notes, job_title=job.title, requirements=requirements
            )
        except LLMRequestError as exc:
            raise InterviewScorecardGenerationError(str(exc)) from exc

        return InterviewScorecardDraft(
            competency_scores=[
                CompetencyScore(
                    competency=item.competency,
                    rating=item.rating,  # type: ignore[arg-type]
                    evidence=item.evidence,
                )
                for item in extraction.competency_scores
            ],
            overall_recommendation=extraction.overall_recommendation,  # type: ignore[arg-type]
            summary=extraction.summary,
        )

    async def save_scorecard(
        self,
        *,
        actor: User,
        permissions: set[str],
        job_id: uuid.UUID,
        application_id: uuid.UUID,
        interview_id: uuid.UUID,
        notes: str,
        competency_scores: list[CompetencyScore],
        overall_recommendation: str,
    ) -> InterviewScorecardRead:
        interview, _, _ = await self._get_interview_for_scoring(
            actor=actor,
            permissions=permissions,
            job_id=job_id,
            application_id=application_id,
            interview_id=interview_id,
        )

        scorecard = await self._scorecards.upsert(
            interview_id=interview.id,
            company_id=actor.company_id,
            submitted_by_user_id=actor.id,
            notes=notes,
            competency_scores=[cs.model_dump() for cs in competency_scores],
            overall_recommendation=overall_recommendation,
            model_used=self._settings.anthropic_model,
            generated_at=datetime.now(timezone.utc),
        )

        # Submitting a scorecard IS the completion signal -- an interviewer who couldn't
        # otherwise mark their own interview complete (gated on interviews.schedule, which they
        # don't hold) now closes that gap as a natural side effect of scoring it.
        if interview.status != "completed":
            interview.status = "completed"
            await self._session.flush()

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="interview.scorecard_submitted",
            target_type="shadow_application",
            target_id=interview.shadow_application_id,
            extra_data={"interview_id": str(interview.id)},
        )
        return self._scorecard_to_read(scorecard)

    async def list_scorecards_for_interview(
        self,
        *,
        actor: User,
        permissions: set[str],
        job_id: uuid.UUID,
        application_id: uuid.UUID,
        interview_id: uuid.UUID,
    ) -> list[InterviewScorecardRead]:
        interview, _, _ = await self._get_interview_for_scoring(
            actor=actor,
            permissions=permissions,
            job_id=job_id,
            application_id=application_id,
            interview_id=interview_id,
        )
        scorecards = await self._scorecards.list_by_interview_id(interview.id)
        return [self._scorecard_to_read(s) for s in scorecards]

    def _scorecard_to_read(self, scorecard: InterviewScorecard) -> InterviewScorecardRead:
        return InterviewScorecardRead(
            id=scorecard.id,
            interview_id=scorecard.interview_id,
            submitted_by_user_id=scorecard.submitted_by_user_id,
            notes=scorecard.notes,
            competency_scores=[
                CompetencyScore.model_validate(cs) for cs in scorecard.competency_scores
            ],
            overall_recommendation=scorecard.overall_recommendation,  # type: ignore[arg-type]
            model_used=scorecard.model_used,
            generated_at=scorecard.generated_at,
        )

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
        return await self._to_read(interview)

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
            interviewer_user_ids = await self._participants.list_user_ids_for_interview(
                interview.id
            )
            summaries.append(
                CandidateInterviewSummary(
                    id=interview.id,
                    application_id=application.id,
                    scheduled_at=interview.scheduled_at,
                    location=interview.location,
                    meeting_link=interview.meeting_link,
                    status=interview.status,  # type: ignore[arg-type]
                    created_at=interview.created_at,
                    interviewer_user_ids=interviewer_user_ids,
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

    async def _get_interview_for_scoring(
        self,
        *,
        actor: User,
        permissions: set[str],
        job_id: uuid.UUID,
        application_id: uuid.UUID,
        interview_id: uuid.UUID,
    ) -> tuple[Interview, ShadowApplication, ShadowJob]:
        """Resource-scoped write access for scorecards: participant-or-scheduler, same shape
        list_for_company already uses for reads, applied here to a write. 404 (not 403) when
        neither holds -- matches this codebase's established "not-found, not forbidden"
        resource-scoping convention."""
        application = await self._get_company_application(
            company_id=actor.company_id, job_id=job_id, application_id=application_id
        )
        job = await self._jobs.get_by_id(application.shadow_job_id)
        if job is None:
            raise ApplicationNotFoundError()
        interview = await self._interviews.get_by_id(interview_id)
        if interview is None or interview.shadow_application_id != application.id:
            raise InterviewNotFoundError()

        if Permissions.INTERVIEWS_SCHEDULE not in permissions:
            if not await self._participants.is_participant(
                interview_id=interview.id, user_id=actor.id
            ):
                raise InterviewNotFoundError()

        return interview, application, job

    async def _validate_interviewers(
        self, *, company_id: uuid.UUID, user_ids: list[uuid.UUID]
    ) -> None:
        for user_id in user_ids:
            if not await self._users.is_company_member(company_id=company_id, user_id=user_id):
                raise InvalidInterviewerError()

    async def _to_read(self, interview: Interview) -> InterviewRead:
        interviewer_user_ids = await self._participants.list_user_ids_for_interview(interview.id)
        return InterviewRead(
            id=interview.id,
            application_id=interview.shadow_application_id,
            scheduled_at=interview.scheduled_at,
            location=interview.location,
            meeting_link=interview.meeting_link,
            status=interview.status,  # type: ignore[arg-type]
            created_at=interview.created_at,
            interviewer_user_ids=interviewer_user_ids,
        )
