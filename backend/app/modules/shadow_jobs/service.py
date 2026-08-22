import logging
import secrets
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.audit.service import AuditService
from app.modules.auth.email import EmailSender, build_added_to_pipeline_email
from app.modules.auth.models import User
from app.modules.candidate_auth.models import CandidateUser
from app.modules.companies.models import Company
from app.modules.companies.service import is_profile_publicly_visible
from app.modules.interviews.repository import InterviewRepository
from app.modules.messages.models import Message
from app.modules.messages.repository import MessageRepository, MessageThreadRepository
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
    ShadowApplicationRead,
    ShadowCareerEntrySummary,
    ShadowJobBoardListing,
    ShadowJobCreate,
    ShadowJobUpdate,
    ShadowProfile,
    ShadowProfileCompanyWide,
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
        self, *, company_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[ShadowJob]:
        return await self._jobs.list_by_company(company_id, limit=limit, offset=offset)

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
            )
            for a in applications
        ]

    async def list_applicants_for_company(self, *, actor: User) -> list[ShadowProfileCompanyWide]:
        """Every applicant across every one of this company's Shadow Jobs, not scoped to one job
        -- powers the centralised cross-project Candidates/Pipeline view. Mirrors list_applicants'
        bulk-lookup shape exactly, just seeded from a company-wide application list and joining
        job title/project per row since the job isn't already known from the URL."""
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

        results: list[ShadowProfileCompanyWide] = []
        for a in applications:
            job = jobs.get(a.shadow_job_id)
            if job is None:
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
        return await self._to_shadow_profile(
            application,
            unread_count=unread_counts.get(application.id, 0),
            has_upcoming_interview=application.id in upcoming_interview_ids,
            talent_pool_status=(
                grant.status
                if (grant := talent_pool_grants.get(application.candidate_user_id)) is not None
                else None
            ),
        )

    async def mark_applicant_viewed(
        self, *, actor: User, job_id: uuid.UUID, application_id: uuid.UUID
    ) -> ShadowProfile:
        await self.get_job_for_company(company_id=actor.company_id, job_id=job_id)
        application = await self._applications.get_by_id(application_id)
        if application is None or application.shadow_job_id != job_id:
            raise ShadowApplicationNotFoundError()

        application = await self._applications.mark_viewed(application)

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

    async def _to_shadow_profile(
        self,
        application: ShadowApplication,
        *,
        unread_count: int = 0,
        has_upcoming_interview: bool = False,
        talent_pool_status: str | None = None,
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
                )
                for entry in career_entries
            ],
            unread_message_count=unread_count,
            has_upcoming_interview=has_upcoming_interview,
            talent_pool_status=talent_pool_status,
            pipeline_stage=application.pipeline_stage,
            effective_stage=effective_stage,
            is_new=application.viewed_at is None,
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

    async def _to_board_listing(self, job: ShadowJob) -> ShadowJobBoardListing:
        company = await self._session.get(Company, job.company_id)
        return ShadowJobBoardListing(
            id=job.id,
            company_name=company.name if company else "Unknown company",
            company_slug=(
                company.slug if company and is_profile_publicly_visible(company) else None
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
