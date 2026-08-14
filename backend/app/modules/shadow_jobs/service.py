import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import AuditService
from app.modules.auth.models import User
from app.modules.candidate_auth.models import CandidateUser
from app.modules.companies.models import Company
from app.modules.phantom_passport.exceptions import PassportNotApprovedError, PassportNotFoundError
from app.modules.phantom_passport.repository import (
    PassportCareerEntryRepository,
    PassportVersionRepository,
    PhantomPassportRepository,
)
from app.modules.phantom_passport.schemas import ShadowProfileSnapshot
from app.modules.shadow_jobs.exceptions import (
    ApplicationAlreadyWithdrawnError,
    CallsignGenerationExhaustedError,
    DuplicateApplicationError,
    PassportRequiredError,
    ShadowApplicationNotFoundError,
    ShadowJobNotFoundError,
    ShadowJobNotPublishedError,
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
)

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
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._jobs = ShadowJobRepository(session)
        self._applications = ShadowApplicationRepository(session)
        self._passports = PhantomPassportRepository(session)
        self._career_entries = PassportCareerEntryRepository(session)
        self._versions = PassportVersionRepository(session)
        self._audit = AuditService(session)

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
        return [await self._to_shadow_profile(a) for a in applications]

    async def _to_shadow_profile(self, application: ShadowApplication) -> ShadowProfile:
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
