import logging
import secrets
import statistics
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.audit.schemas import AuditEntryRead
from app.modules.audit.service import AuditService
from app.modules.auth.email import EmailSender, build_added_to_pipeline_email
from app.modules.auth.models import User
from app.modules.candidate_auth.models import CandidateUser
from app.modules.companies.models import Company
from app.modules.companies.service import CompanyService, is_profile_publicly_visible
from app.modules.interviews.repository import InterviewRepository
from app.modules.messages.models import Message
from app.modules.messages.repository import MessageRepository, MessageThreadRepository
from app.modules.passport_matching.repository import PassportJobMatchRepository
from app.modules.shadow_reveal.repository import ShadowRevealRequestRepository
from app.modules.talent_pool.repository import TalentPoolGrantRepository
from app.modules.phantom_passport.exceptions import PassportNotApprovedError, PassportNotFoundError
from app.modules.phantom_passport.repository import (
    PassportCareerEntryRepository,
    PassportVersionRepository,
    PhantomPassportRepository,
)
from app.modules.phantom_passport.schemas import ShadowProfileSnapshot
from app.modules.shadow_jobs.exceptions import (
    ApplicationAlreadyWithdrawnError,
    ApplicationWithdrawnStageError,
    CallsignGenerationExhaustedError,
    DuplicateApplicationError,
    PassportRequiredError,
    ShadowApplicationNotFoundError,
    ShadowJobNotFoundError,
    ShadowJobNotPendingReviewError,
    ShadowJobNotPublishedError,
    TalentPoolGrantRequiredError,
)
from app.modules.shadow_jobs.models import (
    ShadowApplication,
    ShadowApplicationStatus,
    ShadowJob,
    ShadowJobStatus,
)
from app.modules.shadow_jobs.repository import ShadowApplicationRepository, ShadowJobRepository
from app.modules.shadow_jobs.schemas import (
    JobIntelligence,
    SalaryBenchmark,
    ShadowApplicationRead,
    ShadowCareerEntrySummary,
    ShadowJobBoardListing,
    ShadowJobCreate,
    ShadowJobUpdate,
    ShadowProfile,
    ShadowProfileCompanyWide,
    ViewTimeBenchmark,
)

logger = logging.getLogger("app.shadow_jobs.service")

# Deliberately a separate word pool from identity_vault's — Shadow Callsigns (per job
# application, marketplace-side) and ATS Callsigns (per project, for candidates a recruiter
# added directly) are two independent identity systems by design, see shadow_jobs/__init__.py
# and identity_vault/service.py. Sharing the module would couple two things the product spec
# treats as conceptually distinct.
_CALLSIGN_WORDS = [
    "Onyx", "Cobalt", "Ember", "Slate", "Quartz", "Indigo", "Rune", "Marlow",
    "Halcyon", "Wraith", "Basalt", "Cipher", "Lumen", "Grove", "Amber", "Fjord",
]  # fmt: skip
_MAX_CALLSIGN_ATTEMPTS = 5

# Minimum sample sizes before Job Intelligence shows a real number rather than "not enough data
# yet" -- a thin bucket would either be statistically meaningless or risk fingerprinting one
# specific company's own listing as "the benchmark". See compute_salary_benchmark/
# compute_view_time_benchmark.
_MIN_SALARY_SAMPLE = 5
_MIN_SALARY_COMPANIES = 3
_MIN_VIEW_TIME_SAMPLE = 5


class ShadowJobService:
    def __init__(self, session: AsyncSession, *, email_sender: EmailSender | None = None) -> None:
        self._session = session
        self._jobs = ShadowJobRepository(session)
        self._applications = ShadowApplicationRepository(session)
        self._passports = PhantomPassportRepository(session)
        self._career_entries = PassportCareerEntryRepository(session)
        self._versions = PassportVersionRepository(session)
        self._audit = AuditService(session)
        # Repositories, not MessageService/InterviewService -- importing either service here
        # would create a circular import (both modules' service.py import from shadow_jobs for
        # the application lookup helpers). The repositories have no such dependency.
        self._message_threads = MessageThreadRepository(session)
        self._messages_repo = MessageRepository(session)
        self._interviews = InterviewRepository(session)
        self._talent_pool_grants = TalentPoolGrantRepository(session)
        self._reveal_requests = ShadowRevealRequestRepository(session)
        self._matches = PassportJobMatchRepository(session)
        self._email_sender = email_sender
        self._settings = get_settings()

    # --- Company-side job management --------------------------------------------------------

    async def create_job(self, *, actor: User, body: ShadowJobCreate) -> ShadowJob:
        job = await self._jobs.create(
            company_id=actor.company_id,
            created_by_id=actor.id,
            title=body.title,
            department=body.department,
            seniority=body.seniority,
            employment_type=body.employment_type.value,
            location=body.location,
            remote_preference=body.remote_preference,
            salary_min=body.salary_min,
            salary_max=body.salary_max,
            summary=body.summary,
            description=body.description,
            requirements=body.requirements,
            project_id=body.project_id,
        )
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="shadow_job.created",
            target_type="shadow_job",
            target_id=job.id,
        )
        return job

    async def get_job_for_company(self, *, company_id: uuid.UUID, job_id: uuid.UUID) -> ShadowJob:
        job = await self._jobs.get_by_id(job_id)
        if job is None or job.company_id != company_id or job.deleted_at is not None:
            raise ShadowJobNotFoundError()
        return job

    async def list_jobs_for_company(
        self,
        *,
        company_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        accessible_project_ids: list[uuid.UUID] | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> list[ShadowJob]:
        return await self._jobs.list_by_company(
            company_id,
            limit=limit,
            offset=offset,
            accessible_project_ids=accessible_project_ids,
            actor_id=actor_id,
        )

    async def update_job(
        self, *, actor: User, job_id: uuid.UUID, body: ShadowJobUpdate
    ) -> ShadowJob:
        job = await self.get_job_for_company(company_id=actor.company_id, job_id=job_id)
        fields_set = body.model_fields_set
        for field in fields_set:
            value = getattr(body, field)
            setattr(job, field, value.value if hasattr(value, "value") else value)

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="shadow_job.updated",
            target_type="shadow_job",
            target_id=job.id,
        )
        return job

    async def submit_for_review(self, *, actor: User, job_id: uuid.UUID) -> ShadowJob:
        """Recruiter-facing action -- lands the job in the platform-admin review queue rather
        than going live immediately (see approve_pending_job/reject_pending_job below, the actual
        gate). Named/audited distinctly from publish_job since it no longer publishes anything."""
        job = await self.get_job_for_company(company_id=actor.company_id, job_id=job_id)
        job.status = ShadowJobStatus.PENDING_REVIEW.value
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="shadow_job.submitted_for_review",
            target_type="shadow_job",
            target_id=job.id,
        )
        return job

    async def publish_job(self, *, actor: User, job_id: uuid.UUID) -> ShadowJob:
        job = await self.get_job_for_company(company_id=actor.company_id, job_id=job_id)
        job.status = ShadowJobStatus.PUBLISHED.value
        job.published_at = datetime.now(timezone.utc)
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="shadow_job.published",
            target_type="shadow_job",
            target_id=job.id,
        )
        return job

    async def get_job_any_company(self, job_id: uuid.UUID) -> ShadowJob:
        """No company scoping -- used by the platform-admin review queue, which operates across
        every company's jobs."""
        job = await self._jobs.get_by_id(job_id)
        if job is None or job.deleted_at is not None:
            raise ShadowJobNotFoundError()
        return job

    async def approve_pending_job(self, *, job_id: uuid.UUID) -> ShadowJob:
        """The actual approval gate. Publishing here (not moving the recruiter's own publish
        button) is deliberate -- alert emails must only fire once a job is genuinely public, not
        the moment a recruiter submits it. The authoritative "who approved this" record is the
        PlatformAdminAuditLog entry the caller (platform_admin/jobs_api.py) writes separately;
        this company-side entry has no actor_user_id since a platform admin isn't a company user."""
        job = await self.get_job_any_company(job_id)
        if job.status != ShadowJobStatus.PENDING_REVIEW.value:
            raise ShadowJobNotPendingReviewError()
        job.status = ShadowJobStatus.PUBLISHED.value
        job.published_at = datetime.now(timezone.utc)
        await self._audit.record(
            company_id=job.company_id,
            actor_user_id=None,
            action="shadow_job.published",
            target_type="shadow_job",
            target_id=job.id,
            extra_data={"reviewed_by": "platform_admin"},
        )
        return job

    async def reject_pending_job(self, *, job_id: uuid.UUID) -> ShadowJob:
        job = await self.get_job_any_company(job_id)
        if job.status != ShadowJobStatus.PENDING_REVIEW.value:
            raise ShadowJobNotPendingReviewError()
        job.status = ShadowJobStatus.DRAFT.value
        await self._audit.record(
            company_id=job.company_id,
            actor_user_id=None,
            action="shadow_job.rejected",
            target_type="shadow_job",
            target_id=job.id,
            extra_data={"reviewed_by": "platform_admin"},
        )
        return job

    async def list_pending_review(self) -> list[ShadowJob]:
        return await self._jobs.list_by_status(ShadowJobStatus.PENDING_REVIEW.value)

    async def list_admin_jobs(
        self, *, status: str | None = None, company_id: uuid.UUID | None = None
    ) -> list[ShadowJob]:
        """Powers the platform-admin Jobs list -- spans every company by default, optionally
        filtered to one status and/or one company (the latter for the Company Command Profile's
        Jobs tab). status=None and company_id=None returns every non-deleted job."""
        return await self._jobs.list_all(status=status, company_id=company_id)

    async def get_admin_job_metrics(
        self, job: ShadowJob
    ) -> tuple[int, int, JobIntelligence | None]:
        """(match_count, interview_count, job_intelligence) for the platform-admin job detail
        page. match_count counts already-computed PassportJobMatch rows -- not a total
        addressable count, since matches are computed lazily, not for every discoverable
        candidate up front. job_intelligence is only ever real for a published job (see
        get_job_intelligence's own guard)."""
        applications = await self._applications.list_by_job(job.id)
        application_ids = [a.id for a in applications]
        interview_count = len(await self._interviews.list_by_application_ids(application_ids))
        match_count = await self._matches.count_by_shadow_job_id(job.id)
        job_intelligence = (
            await self.get_job_intelligence(job.id)
            if job.status == ShadowJobStatus.PUBLISHED.value
            else None
        )
        return match_count, interview_count, job_intelligence

    async def publish_project_to_shadow(
        self, *, actor: User, project_id: uuid.UUID, body: ShadowJobCreate
    ) -> ShadowJob:
        """The ATS -> Shadow publish pipeline: an explicit, one-time snapshot. Copies whatever the
        recruiter confirmed in the publish dialog onto the linked ShadowJob (creating it on first
        publish, overwriting the existing one on a re-publish) -- nothing auto-propagates from the
        Project afterward, by design. Orchestrates the existing create/update/publish methods
        rather than duplicating their repository or audit-logging logic."""
        existing = await self._jobs.get_by_project_id(project_id)
        if existing is None:
            job = await self.create_job(
                actor=actor, body=body.model_copy(update={"project_id": project_id})
            )
        else:
            update_body = ShadowJobUpdate(
                title=body.title,
                department=body.department,
                seniority=body.seniority,
                employment_type=body.employment_type,
                location=body.location,
                remote_preference=body.remote_preference,
                salary_min=body.salary_min,
                salary_max=body.salary_max,
                summary=body.summary,
                description=body.description,
                requirements=body.requirements,
            )
            job = await self.update_job(actor=actor, job_id=existing.id, body=update_body)
        # Lands in the review queue, not live -- safe to call unconditionally on a re-publish too;
        # an already-published job re-entering review on every edit is deliberate, not a bug (see
        # the plan this shipped under: admin approval is a real gate, not a one-time formality).
        return await self.submit_for_review(actor=actor, job_id=job.id)

    async def close_job(self, *, actor: User, job_id: uuid.UUID) -> ShadowJob:
        job = await self.get_job_for_company(company_id=actor.company_id, job_id=job_id)
        job.status = ShadowJobStatus.CLOSED.value
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="shadow_job.closed",
            target_type="shadow_job",
            target_id=job.id,
        )
        return job

    async def get_applicant_count(self, job_id: uuid.UUID) -> int:
        return await self._applications.count_by_job(job_id)

    async def list_applicants(
        self, *, company_id: uuid.UUID, job_id: uuid.UUID
    ) -> list[ShadowProfile]:
        await self.get_job_for_company(company_id=company_id, job_id=job_id)
        applications = await self._applications.list_by_job(job_id)
        application_ids = [a.id for a in applications]
        unread_counts = await self._unread_counts_for_applications(application_ids)
        upcoming_interview_ids = {
            i.shadow_application_id
            for i in await self._interviews.list_upcoming_by_application_ids(application_ids)
        }
        talent_pool_grants = await self._talent_pool_grants.list_latest_by_company_and_candidates(
            company_id=company_id, candidate_user_ids=[a.candidate_user_id for a in applications]
        )
        reveal_unseen = await self._reveal_response_unseen_for_applications(application_ids)
        return [
            await self._to_shadow_profile(
                a,
                unread_count=unread_counts.get(a.id, 0),
                has_upcoming_interview=a.id in upcoming_interview_ids,
                talent_pool_status=(
                    grant.status
                    if (grant := talent_pool_grants.get(a.candidate_user_id)) is not None
                    else None
                ),
                reveal_response_is_new=a.id in reveal_unseen,
            )
            for a in applications
        ]

    async def get_applicant(
        self, *, company_id: uuid.UUID, job_id: uuid.UUID, application_id: uuid.UUID
    ) -> ShadowProfile:
        """Single-item sibling of list_applicants -- powers the dedicated per-applicant
        workspace page. Pure read, no side effect (mark-viewed stays its own explicit action,
        triggered client-side, same as it already is for the card-list view)."""
        await self.get_job_for_company(company_id=company_id, job_id=job_id)
        application = await self._applications.get_by_id(application_id)
        if application is None or application.shadow_job_id != job_id:
            raise ShadowApplicationNotFoundError()

        unread_counts = await self._unread_counts_for_applications([application.id])
        upcoming_interview_ids = {
            i.shadow_application_id
            for i in await self._interviews.list_upcoming_by_application_ids([application.id])
        }
        talent_pool_grants = await self._talent_pool_grants.list_latest_by_company_and_candidates(
            company_id=company_id, candidate_user_ids=[application.candidate_user_id]
        )
        reveal_unseen = await self._reveal_response_unseen_for_applications([application.id])
        return await self._to_shadow_profile(
            application,
            unread_count=unread_counts.get(application.id, 0),
            has_upcoming_interview=application.id in upcoming_interview_ids,
            talent_pool_status=(
                grant.status
                if (grant := talent_pool_grants.get(application.candidate_user_id)) is not None
                else None
            ),
            reveal_response_is_new=application.id in reveal_unseen,
        )

    async def list_applicant_activity(
        self, *, actor: User, job_id: uuid.UUID, application_id: uuid.UUID
    ) -> list[AuditEntryRead]:
        """Real audit trail for one applicant -- every shadow_application-targeted AuditLog row
        (application submitted/added/withdrawn/pipeline-stage-updated, reveal requested/
        approved/declined, message sent, interview scheduled/rescheduled/cancelled/completed).
        Deliberately excludes talent_pool.* events, which target the grant row, not the
        application -- a real, small scope cut rather than a join worth adding for one edge case."""
        await self.get_job_for_company(company_id=actor.company_id, job_id=job_id)
        application = await self._applications.get_by_id(application_id)
        if application is None or application.shadow_job_id != job_id:
            raise ShadowApplicationNotFoundError()
        return await self._audit.list_by_target(
            company_id=actor.company_id,
            target_type="shadow_application",
            target_id=application.id,
        )

    async def list_applicants_for_company(
        self, *, actor: User, accessible_project_ids: list[uuid.UUID] | None = None
    ) -> list[ShadowProfileCompanyWide]:
        """Every applicant across every one of this company's Shadow Jobs, not scoped to one job
        -- powers the centralised cross-project Candidates/Pipeline view. Mirrors list_applicants'
        bulk-lookup shape exactly, just seeded from a company-wide application list and joining
        job title/project per row since the job isn't already known from the URL.

        accessible_project_ids (None for Owner/Admin, a Member's accessible project ids
        otherwise) applies the same resource-level scoping list_jobs_for_company does -- an
        applicant is only included if their job is linked to one of those projects, or is a
        project-less job the actor themselves created."""
        applications = await self._applications.list_by_company_id(actor.company_id)
        application_ids = [a.id for a in applications]
        unread_counts = await self._unread_counts_for_applications(application_ids)
        upcoming_interview_ids = {
            i.shadow_application_id
            for i in await self._interviews.list_upcoming_by_application_ids(application_ids)
        }
        talent_pool_grants = await self._talent_pool_grants.list_latest_by_company_and_candidates(
            company_id=actor.company_id,
            candidate_user_ids=[a.candidate_user_id for a in applications],
        )
        job_ids = {a.shadow_job_id for a in applications}
        jobs = {job_id: await self._jobs.get_by_id(job_id) for job_id in job_ids}
        reveal_unseen = await self._reveal_response_unseen_for_applications(application_ids)

        results: list[ShadowProfileCompanyWide] = []
        for a in applications:
            job = jobs.get(a.shadow_job_id)
            if job is None:
                continue
            if accessible_project_ids is not None and not (
                job.project_id in accessible_project_ids
                or (job.project_id is None and job.created_by_id == actor.id)
            ):
                continue
            profile = await self._to_shadow_profile(
                a,
                unread_count=unread_counts.get(a.id, 0),
                has_upcoming_interview=a.id in upcoming_interview_ids,
                talent_pool_status=(
                    grant.status
                    if (grant := talent_pool_grants.get(a.candidate_user_id)) is not None
                    else None
                ),
                reveal_response_is_new=a.id in reveal_unseen,
            )
            results.append(
                ShadowProfileCompanyWide(
                    **profile.model_dump(),
                    shadow_job_id=job.id,
                    job_title=job.title,
                    project_id=job.project_id,
                )
            )
        return results

    async def update_applicant_pipeline_stage(
        self,
        *,
        actor: User,
        job_id: uuid.UUID,
        application_id: uuid.UUID,
        pipeline_stage: str,
    ) -> ShadowProfile:
        await self.get_job_for_company(company_id=actor.company_id, job_id=job_id)
        application = await self._applications.get_by_id(application_id)
        if application is None or application.shadow_job_id != job_id:
            raise ShadowApplicationNotFoundError()
        if application.status == ShadowApplicationStatus.WITHDRAWN.value:
            raise ApplicationWithdrawnStageError()

        application = await self._applications.update_pipeline_stage(
            application, pipeline_stage=pipeline_stage
        )
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="shadow_application.pipeline_stage_updated",
            target_type="shadow_application",
            target_id=application.id,
            extra_data={"pipeline_stage": pipeline_stage},
        )

        unread_counts = await self._unread_counts_for_applications([application.id])
        upcoming_interview_ids = {
            i.shadow_application_id
            for i in await self._interviews.list_upcoming_by_application_ids([application.id])
        }
        talent_pool_grants = await self._talent_pool_grants.list_latest_by_company_and_candidates(
            company_id=actor.company_id, candidate_user_ids=[application.candidate_user_id]
        )
        reveal_unseen = await self._reveal_response_unseen_for_applications([application.id])
        return await self._to_shadow_profile(
            application,
            unread_count=unread_counts.get(application.id, 0),
            has_upcoming_interview=application.id in upcoming_interview_ids,
            talent_pool_status=(
                grant.status
                if (grant := talent_pool_grants.get(application.candidate_user_id)) is not None
                else None
            ),
            reveal_response_is_new=application.id in reveal_unseen,
        )

    async def mark_applicant_viewed(
        self, *, actor: User, job_id: uuid.UUID, application_id: uuid.UUID
    ) -> ShadowProfile:
        await self.get_job_for_company(company_id=actor.company_id, job_id=job_id)
        application = await self._applications.get_by_id(application_id)
        if application is None or application.shadow_job_id != job_id:
            raise ShadowApplicationNotFoundError()

        application = await self._applications.mark_viewed(application)

        # Opening the card acknowledges everything about it -- also clears an unseen reveal
        # response, if one's sitting there, rather than requiring a separate "mark viewed" action.
        # A still-pending request has nothing to acknowledge yet, so it's deliberately left alone
        # (marking it now would make a later real response wrongly start out already "seen").
        reveal_request = await self._reveal_requests.get_by_application_id(application.id)
        if reveal_request is not None and reveal_request.status != "pending":
            await self._reveal_requests.mark_company_viewed(reveal_request)

        unread_counts = await self._unread_counts_for_applications([application.id])
        upcoming_interview_ids = {
            i.shadow_application_id
            for i in await self._interviews.list_upcoming_by_application_ids([application.id])
        }
        talent_pool_grants = await self._talent_pool_grants.list_latest_by_company_and_candidates(
            company_id=actor.company_id, candidate_user_ids=[application.candidate_user_id]
        )
        return await self._to_shadow_profile(
            application,
            unread_count=unread_counts.get(application.id, 0),
            has_upcoming_interview=application.id in upcoming_interview_ids,
            talent_pool_status=(
                grant.status
                if (grant := talent_pool_grants.get(application.candidate_user_id)) is not None
                else None
            ),
            reveal_response_is_new=False,
        )

    async def _unread_counts_for_applications(
        self, application_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, int]:
        """One bulk lookup for the whole applicant list, not one per card -- see
        messages/service.py's MessageService.unread_counts_for_applications for the identical
        shape (duplicated here rather than imported to avoid a circular import, see __init__)."""
        if not application_ids:
            return {}
        threads = await self._message_threads.list_by_application_ids(application_ids)
        thread_by_app = {t.shadow_application_id: t for t in threads}
        thread_ids = [t.id for t in threads]
        candidate_messages = await self._messages_repo.list_candidate_messages_for_threads(
            thread_ids
        )
        by_thread: dict[uuid.UUID, list[Message]] = defaultdict(list)
        for message in candidate_messages:
            by_thread[message.thread_id].append(message)

        counts: dict[uuid.UUID, int] = {}
        for app_id in application_ids:
            thread = thread_by_app.get(app_id)
            if thread is None:
                counts[app_id] = 0
                continue
            cutoff = thread.company_last_read_at
            counts[app_id] = sum(
                1 for m in by_thread.get(thread.id, []) if cutoff is None or m.created_at > cutoff
            )
        return counts

    async def _reveal_response_unseen_for_applications(
        self, application_ids: list[uuid.UUID]
    ) -> set[uuid.UUID]:
        """One bulk lookup for the whole applicant list -- which applications have a reveal
        response (approved/declined) nobody's opened the card for since. Same shape as
        _unread_counts_for_applications."""
        requests = await self._reveal_requests.list_by_application_ids(application_ids)
        return {
            r.shadow_application_id
            for r in requests
            if r.status != "pending" and r.company_viewed_at is None
        }

    async def _to_shadow_profile(
        self,
        application: ShadowApplication,
        *,
        unread_count: int = 0,
        has_upcoming_interview: bool = False,
        talent_pool_status: str | None = None,
        reveal_response_is_new: bool = False,
    ) -> ShadowProfile:
        effective_stage = (
            ShadowApplicationStatus.WITHDRAWN.value
            if application.status == ShadowApplicationStatus.WITHDRAWN.value
            else application.pipeline_stage
        )
        # An application with a recorded passport_version_id is frozen to exactly what the
        # candidate had approved at apply time — a later Passport edit/re-approval must not
        # retroactively change what a recruiter sees here. Only applications submitted before
        # this column existed (passport_version_id is null, pre-launch dev rows) fall back to a
        # live read, matching this method's original behavior.
        if application.passport_version_id is not None:
            version = await self._versions.get_by_id(application.passport_version_id)
            if version is not None:
                snapshot = ShadowProfileSnapshot.model_validate(version.snapshot)
                return ShadowProfile(
                    application_id=application.id,
                    callsign=application.callsign,
                    status=ShadowApplicationStatus(application.status),
                    applied_at=application.created_at,
                    headline=snapshot.headline,
                    seniority=snapshot.seniority,
                    years_experience=snapshot.years_experience,
                    summary=snapshot.summary,
                    skills=snapshot.skills,
                    industries=snapshot.industries,
                    location=snapshot.location,
                    remote_preference=snapshot.remote_preference,
                    salary_min=snapshot.salary_min,
                    salary_max=snapshot.salary_max,
                    notice_period=snapshot.notice_period,
                    career_intent=snapshot.career_intent,
                    career_entries=[
                        ShadowCareerEntrySummary(**entry) for entry in snapshot.career_entries
                    ],
                    unread_message_count=unread_count,
                    has_upcoming_interview=has_upcoming_interview,
                    talent_pool_status=talent_pool_status,
                    pipeline_stage=application.pipeline_stage,
                    effective_stage=effective_stage,
                    is_new=application.viewed_at is None,
                    reveal_response_is_new=reveal_response_is_new,
                    revealed_full_name=application.revealed_full_name,
                    revealed_email=application.revealed_email,
                    revealed_phone=application.revealed_phone,
                    revealed_career_entries=application.revealed_career_entries,
                )

        # Reuses phantom_passport's own repositories rather than querying PhantomPassport
        # columns by hand — and never touches PassportPersonalInfoRepository at all, so there is
        # no code path here that could even attempt to read a candidate's name, email, or phone.
        passport = await self._passports.get_by_candidate_user_id(application.candidate_user_id)
        if passport is None:
            raise PassportNotFoundError()
        career_entries = await self._career_entries.list_by_passport_id(passport.id)

        return ShadowProfile(
            application_id=application.id,
            callsign=application.callsign,
            status=ShadowApplicationStatus(application.status),
            applied_at=application.created_at,
            headline=passport.headline,
            seniority=passport.seniority,
            years_experience=passport.years_experience,
            summary=passport.summary,
            skills=list(passport.skills),
            industries=list(passport.industries),
            location=passport.location,
            remote_preference=passport.remote_preference,
            salary_min=passport.salary_min,
            salary_max=passport.salary_max,
            notice_period=passport.notice_period,
            career_intent=passport.career_intent,
            career_entries=[
                ShadowCareerEntrySummary(
                    title=entry.title,
                    company_name_anonymized=entry.company_name_anonymized,
                    is_current=entry.is_current,
                    start_date=entry.start_date,
                    end_date=entry.end_date,
                    responsibilities=entry.responsibilities,
                    achievements=list(entry.achievements),
                )
                for entry in career_entries
            ],
            unread_message_count=unread_count,
            has_upcoming_interview=has_upcoming_interview,
            talent_pool_status=talent_pool_status,
            pipeline_stage=application.pipeline_stage,
            effective_stage=effective_stage,
            is_new=application.viewed_at is None,
            reveal_response_is_new=reveal_response_is_new,
            revealed_full_name=application.revealed_full_name,
            revealed_email=application.revealed_email,
            revealed_phone=application.revealed_phone,
            revealed_career_entries=application.revealed_career_entries,
        )

    # --- Public job board ---------------------------------------------------------------------

    async def browse_board(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        seniority: str | None = None,
        remote_preference: str | None = None,
        employment_type: str | None = None,
        location: str | None = None,
    ) -> list[ShadowJobBoardListing]:
        jobs = await self._jobs.list_published(
            limit=limit,
            offset=offset,
            seniority=seniority,
            remote_preference=remote_preference,
            employment_type=employment_type,
            location=location,
        )
        return [await self._to_board_listing(job) for job in jobs]

    async def get_board_detail(self, job_id: uuid.UUID) -> ShadowJobBoardListing:
        job = await self._jobs.get_by_id(job_id)
        if (
            job is None
            or job.deleted_at is not None
            or job.status != ShadowJobStatus.PUBLISHED.value
        ):
            raise ShadowJobNotFoundError()
        return await self._to_board_listing(job)

    async def get_job_intelligence(self, job_id: uuid.UUID) -> JobIntelligence:
        job = await self._jobs.get_by_id(job_id)
        if (
            job is None
            or job.deleted_at is not None
            or job.status != ShadowJobStatus.PUBLISHED.value
        ):
            raise ShadowJobNotFoundError()
        return JobIntelligence(
            salary_benchmark=await self.compute_salary_benchmark(job),
            view_time_benchmark=await self.compute_view_time_benchmark(job.company_id),
        )

    async def compute_salary_benchmark(self, job: ShadowJob) -> SalaryBenchmark:
        """Real aggregation over other published jobs with the same employment_type and (when set)
        a case-insensitive seniority match. Gated on a minimum sample size (see module-level
        _MIN_SALARY_SAMPLE/_MIN_SALARY_COMPANIES) so a thin bucket never produces a misleading
        single-data-point "benchmark", or fingerprints one specific company's own listing."""
        candidates = await self._jobs.list_published(
            limit=500, employment_type=job.employment_type
        )
        if job.seniority:
            candidates = [
                c
                for c in candidates
                if c.seniority and c.seniority.strip().lower() == job.seniority.strip().lower()
            ]
        candidates = [c for c in candidates if c.id != job.id]

        midpoints: list[float] = []
        company_ids: set[uuid.UUID] = set()
        for candidate in candidates:
            if candidate.salary_min is None and candidate.salary_max is None:
                continue
            if candidate.salary_min is not None and candidate.salary_max is not None:
                midpoints.append((candidate.salary_min + candidate.salary_max) / 2)
            elif candidate.salary_min is not None:
                midpoints.append(float(candidate.salary_min))
            else:
                assert candidate.salary_max is not None
                midpoints.append(float(candidate.salary_max))
            company_ids.add(candidate.company_id)

        if len(midpoints) < _MIN_SALARY_SAMPLE or len(company_ids) < _MIN_SALARY_COMPANIES:
            return SalaryBenchmark(
                has_enough_data=False, sample_size=len(midpoints), company_count=len(company_ids)
            )

        median = statistics.median(midpoints)
        this_job_midpoint: float | None = None
        if job.salary_min is not None and job.salary_max is not None:
            this_job_midpoint = (job.salary_min + job.salary_max) / 2
        elif job.salary_min is not None:
            this_job_midpoint = float(job.salary_min)
        elif job.salary_max is not None:
            this_job_midpoint = float(job.salary_max)

        vs_median: Literal["above", "at", "below"] | None = None
        if this_job_midpoint is not None:
            if this_job_midpoint > median:
                vs_median = "above"
            elif this_job_midpoint < median:
                vs_median = "below"
            else:
                vs_median = "at"

        return SalaryBenchmark(
            has_enough_data=True,
            sample_size=len(midpoints),
            company_count=len(company_ids),
            median=round(median),
            this_job_vs_median=vs_median,
        )

    async def compute_view_time_benchmark(self, company_id: uuid.UUID) -> ViewTimeBenchmark:
        """Reuses the real, already-populated ShadowApplication.viewed_at column, framed as "time
        to first view" rather than "response time" -- no event in this codebase captures an actual
        recruiter decision/reply, only a first card-open. Aggregated across every job the company
        has posted, not just one, so the sample has a realistic chance of clearing the threshold."""
        applications = await self._applications.list_by_company_id(company_id)
        hours: list[float] = [
            (application.viewed_at - application.created_at).total_seconds() / 3600
            for application in applications
            if application.viewed_at is not None
        ]

        if len(hours) < _MIN_VIEW_TIME_SAMPLE:
            return ViewTimeBenchmark(has_enough_data=False, sample_size=len(hours))

        return ViewTimeBenchmark(
            has_enough_data=True,
            sample_size=len(hours),
            median_hours=round(statistics.median(hours), 1),
        )

    async def _to_board_listing(self, job: ShadowJob) -> ShadowJobBoardListing:
        company = await self._session.get(Company, job.company_id)
        return ShadowJobBoardListing(
            id=job.id,
            company_name=company.name if company else "Unknown company",
            company_slug=(
                company.slug if company and is_profile_publicly_visible(company) else None
            ),
            is_verified_employer=company.is_verified_employer if company else False,
            logo_url=(
                CompanyService._media_url(company.slug, "logo", company.logo_storage_key)
                if company
                else None
            ),
            title=job.title,
            department=job.department,
            seniority=job.seniority,
            employment_type=job.employment_type,
            location=job.location,
            remote_preference=job.remote_preference,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            summary=job.summary,
            description=job.description,
            requirements=list(job.requirements),
            published_at=job.published_at,
        )

    # --- Apply with Phantom Passport -----------------------------------------------------------

    async def apply(self, *, candidate: CandidateUser, job_id: uuid.UUID) -> ShadowApplicationRead:
        job = await self._jobs.get_by_id(job_id)
        if job is None or job.deleted_at is not None:
            raise ShadowJobNotFoundError()
        if job.status != ShadowJobStatus.PUBLISHED.value:
            raise ShadowJobNotPublishedError()

        passport = await self._passports.get_by_candidate_user_id(candidate.id)
        if passport is None:
            raise PassportRequiredError()
        if passport.current_version_id is None:
            raise PassportNotApprovedError()

        existing = await self._applications.get_by_job_and_candidate(
            shadow_job_id=job.id, candidate_user_id=candidate.id
        )
        if existing is not None:
            raise DuplicateApplicationError()

        callsign = await self._generate_callsign(job.id)
        application = await self._applications.create(
            company_id=job.company_id,
            shadow_job_id=job.id,
            candidate_user_id=candidate.id,
            phantom_passport_id=passport.id,
            passport_version_id=passport.current_version_id,
            callsign=callsign,
        )
        # actor_user_id is None — the acting principal is a CandidateUser, not a company User,
        # and audit_logs.actor_user_id is a FK to users only. The company still needs this event
        # in its own audit trail, so it's recorded under the job's company_id regardless.
        await self._audit.record(
            company_id=job.company_id,
            actor_user_id=None,
            action="shadow_application.submitted",
            target_type="shadow_application",
            target_id=application.id,
            extra_data={"callsign": callsign, "shadow_job_id": str(job.id)},
        )

        company = await self._session.get(Company, job.company_id)
        return ShadowApplicationRead(
            id=application.id,
            shadow_job_id=job.id,
            job_title=job.title,
            company_name=company.name if company else "Unknown company",
            callsign=application.callsign,
            status=ShadowApplicationStatus(application.status),
            applied_at=application.created_at,
        )

    async def apply_on_behalf(
        self, *, actor: User, job_id: uuid.UUID, callsign: str
    ) -> ShadowApplicationRead:
        """Recruiter-triggered application for a candidate who already has a GRANTED Talent Pool
        relationship with this company -- reuses their approved Passport exactly like their own
        one-click apply, but requires real, standing consent rather than acting on a stranger's
        profile. The replacement for manually creating a brand-new ATS Candidate row: any
        candidate reachable this way already has a Phantom Passport and already said "consider me
        for future roles here."
        """
        job = await self.get_job_for_company(company_id=actor.company_id, job_id=job_id)
        if job.status != ShadowJobStatus.PUBLISHED.value:
            raise ShadowJobNotPublishedError()

        passport = await self._passports.get_by_callsign(callsign)
        if passport is None:
            raise PassportNotFoundError()

        grant = await self._talent_pool_grants.get_granted_eligible_for_project(
            candidate_user_id=passport.candidate_user_id,
            company_id=actor.company_id,
            project_id=job.project_id,
        )
        if grant is None:
            raise TalentPoolGrantRequiredError()

        if passport.current_version_id is None:
            raise PassportNotApprovedError()

        existing = await self._applications.get_by_job_and_candidate(
            shadow_job_id=job.id, candidate_user_id=passport.candidate_user_id
        )
        if existing is not None:
            raise DuplicateApplicationError()

        new_callsign = await self._generate_callsign(job.id)
        application = await self._applications.create(
            company_id=job.company_id,
            shadow_job_id=job.id,
            candidate_user_id=passport.candidate_user_id,
            phantom_passport_id=passport.id,
            passport_version_id=passport.current_version_id,
            callsign=new_callsign,
        )
        await self._audit.record(
            company_id=job.company_id,
            actor_user_id=actor.id,
            action="shadow_application.added_by_recruiter",
            target_type="shadow_application",
            target_id=application.id,
            extra_data={
                "callsign": new_callsign,
                "shadow_job_id": str(job.id),
                "talent_pool_grant_id": str(grant.id),
            },
        )
        await self._notify_candidate_of_pipeline_add(
            candidate_user_id=passport.candidate_user_id,
            company_id=job.company_id,
            role_title=job.title,
        )

        company = await self._session.get(Company, job.company_id)
        return ShadowApplicationRead(
            id=application.id,
            shadow_job_id=job.id,
            job_title=job.title,
            company_name=company.name if company else "Unknown company",
            callsign=application.callsign,
            status=ShadowApplicationStatus(application.status),
            applied_at=application.created_at,
        )

    async def create_application_from_introduction(
        self, *, candidate: CandidateUser, job_id: uuid.UUID
    ) -> ShadowApplicationRead:
        """Powers accepting a Request Introduction (shadow_introduction module) -- a get-or-create
        variant of apply(): if the candidate already has a real application for this job (e.g.
        they separately applied while the introduction was pending), that existing row is reused
        rather than erroring, since accepting an introduction should always succeed once the
        candidate says yes. Otherwise this is apply()'s exact body (passport-approved gate,
        callsign generation), audited under a distinct action so an introduction-created
        application stays traceable while remaining structurally identical to a self-submitted
        one. Purely additive -- apply() itself is untouched."""
        job = await self._jobs.get_by_id(job_id)
        if job is None or job.deleted_at is not None:
            raise ShadowJobNotFoundError()

        passport = await self._passports.get_by_candidate_user_id(candidate.id)
        if passport is None:
            raise PassportRequiredError()
        if passport.current_version_id is None:
            raise PassportNotApprovedError()

        existing = await self._applications.get_by_job_and_candidate(
            shadow_job_id=job.id, candidate_user_id=candidate.id
        )
        if existing is not None:
            company = await self._session.get(Company, job.company_id)
            return ShadowApplicationRead(
                id=existing.id,
                shadow_job_id=job.id,
                job_title=job.title,
                company_name=company.name if company else "Unknown company",
                callsign=existing.callsign,
                status=ShadowApplicationStatus(existing.status),
                applied_at=existing.created_at,
            )

        callsign = await self._generate_callsign(job.id)
        application = await self._applications.create(
            company_id=job.company_id,
            shadow_job_id=job.id,
            candidate_user_id=candidate.id,
            phantom_passport_id=passport.id,
            passport_version_id=passport.current_version_id,
            callsign=callsign,
        )
        await self._audit.record(
            company_id=job.company_id,
            actor_user_id=None,
            action="shadow_application.introduction_accepted",
            target_type="shadow_application",
            target_id=application.id,
            extra_data={"callsign": callsign, "shadow_job_id": str(job.id)},
        )

        company = await self._session.get(Company, job.company_id)
        return ShadowApplicationRead(
            id=application.id,
            shadow_job_id=job.id,
            job_title=job.title,
            company_name=company.name if company else "Unknown company",
            callsign=application.callsign,
            status=ShadowApplicationStatus(application.status),
            applied_at=application.created_at,
        )

    async def _notify_candidate_of_pipeline_add(
        self, *, candidate_user_id: uuid.UUID, company_id: uuid.UUID, role_title: str
    ) -> None:
        if self._email_sender is None:
            return
        candidate = await self._session.get(CandidateUser, candidate_user_id)
        company = await self._session.get(Company, company_id)
        if candidate is None or company is None:
            return
        applications_url = f"{self._settings.frontend_base_url}/shadow/applications"
        subject, body = build_added_to_pipeline_email(
            company_name=company.name, role_title=role_title, applications_url=applications_url
        )
        try:
            await self._email_sender.send(to=candidate.email, subject=subject, body=body)
        except Exception:
            # A send failure must never fail the request it's riding along with.
            logger.exception("Failed to send pipeline-add email to candidate %s", candidate_user_id)

    async def list_my_applications(
        self, *, candidate: CandidateUser
    ) -> list[ShadowApplicationRead]:
        applications = await self._applications.list_by_candidate(candidate.id)
        results = []
        for application in applications:
            job = await self._jobs.get_by_id(application.shadow_job_id)
            if job is None:
                continue
            company = await self._session.get(Company, job.company_id)
            results.append(
                ShadowApplicationRead(
                    id=application.id,
                    shadow_job_id=job.id,
                    job_title=job.title,
                    company_name=company.name if company else "Unknown company",
                    callsign=application.callsign,
                    status=ShadowApplicationStatus(application.status),
                    applied_at=application.created_at,
                )
            )
        return results

    async def get_my_application(
        self, *, candidate: CandidateUser, application_id: uuid.UUID
    ) -> ShadowApplicationRead:
        application = await self._applications.get_by_id(application_id)
        if application is None or application.candidate_user_id != candidate.id:
            raise ShadowApplicationNotFoundError()
        job = await self._jobs.get_by_id(application.shadow_job_id)
        if job is None:
            raise ShadowApplicationNotFoundError()
        company = await self._session.get(Company, job.company_id)
        return ShadowApplicationRead(
            id=application.id,
            shadow_job_id=job.id,
            job_title=job.title,
            company_name=company.name if company else "Unknown company",
            callsign=application.callsign,
            status=ShadowApplicationStatus(application.status),
            applied_at=application.created_at,
        )

    async def withdraw_application(
        self, *, candidate: CandidateUser, application_id: uuid.UUID
    ) -> ShadowApplicationRead:
        application = await self._applications.get_by_id(application_id)
        if application is None or application.candidate_user_id != candidate.id:
            raise ShadowApplicationNotFoundError()
        if application.status == ShadowApplicationStatus.WITHDRAWN.value:
            raise ApplicationAlreadyWithdrawnError()

        application = await self._applications.update_status(
            application, status=ShadowApplicationStatus.WITHDRAWN.value
        )
        await self._audit.record(
            company_id=application.company_id,
            actor_user_id=None,
            action="shadow_application.withdrawn",
            target_type="shadow_application",
            target_id=application.id,
        )

        job = await self._jobs.get_by_id(application.shadow_job_id)
        company = await self._session.get(Company, job.company_id) if job else None
        return ShadowApplicationRead(
            id=application.id,
            shadow_job_id=application.shadow_job_id,
            job_title=job.title if job else "Unknown role",
            company_name=company.name if company else "Unknown company",
            callsign=application.callsign,
            status=ShadowApplicationStatus(application.status),
            applied_at=application.created_at,
        )

    async def _generate_callsign(self, shadow_job_id: uuid.UUID) -> str:
        for _ in range(_MAX_CALLSIGN_ATTEMPTS):
            callsign = f"{secrets.choice(_CALLSIGN_WORDS)}-{secrets.randbelow(90) + 10}"
            if not await self._applications.callsign_exists_for_job(shadow_job_id, callsign):
                return callsign
        raise CallsignGenerationExhaustedError()
