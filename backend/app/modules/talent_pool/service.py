import logging
import uuid
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.audit.service import AuditService
from app.modules.auth.email import EmailSender, build_talent_pool_request_email
from app.modules.auth.models import User
from app.modules.candidate_auth.models import CandidateUser
from app.modules.candidate_auth.repository import CandidateUserRepository
from app.modules.companies.models import Company
from app.modules.phantom_passport.models import PhantomPassport
from app.modules.phantom_passport.repository import PhantomPassportRepository
from app.modules.projects.exceptions import ProjectNotFoundError
from app.modules.projects.repository import ProjectRepository
from app.modules.shadow_jobs.exceptions import (
    ShadowApplicationNotFoundError,
    ShadowJobNotFoundError,
)
from app.modules.shadow_jobs.models import (
    ShadowApplication,
    ShadowApplicationStatus,
    ShadowJobStatus,
)
from app.modules.shadow_jobs.repository import ShadowApplicationRepository, ShadowJobRepository
from app.modules.talent_pool.exceptions import (
    DuplicateTalentPoolRequestError,
    TalentPoolGrantNotActiveError,
    TalentPoolRequestNotEligibleError,
    TalentPoolRequestNotFoundError,
    TalentPoolRequestNotPendingError,
)
from app.modules.talent_pool.models import TalentPoolGrant, TalentPoolGrantStatus, TalentPoolScope
from app.modules.talent_pool.repository import TalentPoolGrantRepository
from app.modules.talent_pool.schemas import (
    CandidateTalentPoolRequestRead,
    TalentPoolBulkRequestResult,
    TalentPoolBulkSkip,
    TalentPoolDecision,
    TalentPoolGrantRead,
    TalentPoolPoolListItem,
    TalentPoolRequestCreate,
)

logger = logging.getLogger("app.talent_pool.service")

_REVIEW_PERIOD_DAYS = 365

_ELIGIBLE_APPLICATION_STATUSES = {
    ShadowApplicationStatus.DECLINED.value,
    ShadowApplicationStatus.WITHDRAWN.value,
}


def _is_discoverable(passport: PhantomPassport) -> bool:
    """Same eligibility gate as PhantomPassportRepository.list_discoverable_candidates -- a
    bulk-request re-checks this server-side (never trusts a client-held search result) since a
    candidate may have gone private or "not looking" since the search ran."""
    return (
        passport.visibility != "private"
        and passport.career_intent != "not_looking"
        and passport.current_version_id is not None
        and passport.deleted_at is None
    )


class TalentPoolService:
    def __init__(self, session: AsyncSession, *, email_sender: EmailSender | None = None) -> None:
        self._session = session
        self._grants = TalentPoolGrantRepository(session)
        self._applications = ShadowApplicationRepository(session)
        self._jobs = ShadowJobRepository(session)
        self._projects = ProjectRepository(session)
        self._passports = PhantomPassportRepository(session)
        self._candidate_users = CandidateUserRepository(session)
        self._audit = AuditService(session)
        self._email_sender = email_sender
        self._settings = get_settings()

    # --- Company side: request a grant -----------------------------------------------------

    async def request_talent_pool(
        self,
        *,
        actor: User,
        job_id: uuid.UUID,
        application_id: uuid.UUID,
        body: TalentPoolRequestCreate,
    ) -> TalentPoolGrantRead:
        application = await self._get_company_application(
            company_id=actor.company_id, job_id=job_id, application_id=application_id
        )
        job = await self._jobs.get_by_id(job_id)
        if job is None:
            raise ShadowJobNotFoundError()
        if (
            job.status != ShadowJobStatus.CLOSED.value
            and application.status not in _ELIGIBLE_APPLICATION_STATUSES
        ):
            raise TalentPoolRequestNotEligibleError()

        existing = await self._grants.get_active_by_pair(
            candidate_user_id=application.candidate_user_id, company_id=actor.company_id
        )
        if existing is not None:
            raise DuplicateTalentPoolRequestError()

        grant = await self._grants.create(
            candidate_user_id=application.candidate_user_id,
            company_id=actor.company_id,
            source_shadow_application_id=application.id,
            source_project_id=job.project_id,
            source_role_title=job.title,
            requested_by_user_id=actor.id,
            note=body.note,
        )
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="talent_pool.requested",
            target_type="shadow_application",
            target_id=application.id,
            extra_data={"talent_pool_grant_id": str(grant.id)},
        )
        await self._notify_candidate_of_request(
            candidate_user_id=application.candidate_user_id,
            company_id=actor.company_id,
            role_title=job.title,
        )
        return _to_grant_read(grant)

    async def request_talent_pool_bulk(
        self,
        *,
        actor: User,
        job_id: uuid.UUID,
        callsigns: list[str],
        note: str | None,
    ) -> TalentPoolBulkRequestResult:
        """Requesting Talent Pool directly from Search Candidates results -- no application
        exists for these candidates, so source_shadow_application_id is left null (see migration
        0046's nullable + SET NULL treatment, added for exactly this case)."""
        job = await self._jobs.get_by_id(job_id)
        if job is None or job.company_id != actor.company_id or job.deleted_at is not None:
            raise ShadowJobNotFoundError()

        requested: list[str] = []
        skipped: list[TalentPoolBulkSkip] = []
        for callsign in callsigns:
            passport = await self._passports.get_by_callsign(callsign)
            if passport is None or not _is_discoverable(passport):
                skipped.append(
                    TalentPoolBulkSkip(callsign=callsign, reason="No longer discoverable")
                )
                continue

            existing = await self._grants.get_active_by_pair(
                candidate_user_id=passport.candidate_user_id, company_id=actor.company_id
            )
            if existing is not None:
                skipped.append(
                    TalentPoolBulkSkip(callsign=callsign, reason="Already requested or granted")
                )
                continue

            grant = await self._grants.create(
                candidate_user_id=passport.candidate_user_id,
                company_id=actor.company_id,
                source_shadow_application_id=None,
                source_project_id=job.project_id,
                source_role_title=job.title,
                requested_by_user_id=actor.id,
                note=note,
            )
            await self._audit.record(
                company_id=actor.company_id,
                actor_user_id=actor.id,
                action="talent_pool.requested",
                target_type="phantom_passport",
                target_id=passport.id,
                extra_data={"talent_pool_grant_id": str(grant.id), "source": "search_candidates"},
            )
            await self._notify_candidate_of_request(
                candidate_user_id=passport.candidate_user_id,
                company_id=actor.company_id,
                role_title=job.title,
            )
            requested.append(callsign)

        return TalentPoolBulkRequestResult(requested=requested, skipped=skipped)

    async def _notify_candidate_of_request(
        self, *, candidate_user_id: uuid.UUID, company_id: uuid.UUID, role_title: str
    ) -> None:
        if self._email_sender is None:
            return
        candidate = await self._candidate_users.get_by_id(candidate_user_id)
        company = await self._session.get(Company, company_id)
        if candidate is None or company is None:
            return
        requests_url = f"{self._settings.frontend_base_url}/shadow/passport/talent-memory"
        subject, body = build_talent_pool_request_email(
            company_name=company.name, role_title=role_title, requests_url=requests_url
        )
        try:
            await self._email_sender.send(to=candidate.email, subject=subject, body=body)
        except Exception:
            # A send failure must never fail the request it's riding along with.
            logger.exception(
                "Failed to send Talent Pool request email to candidate %s", candidate_user_id
            )

    async def list_company_talent_pool(
        self, *, company_id: uuid.UUID
    ) -> list[TalentPoolPoolListItem]:
        grants = await self._grants.list_granted_by_company_id(company_id)
        items: list[TalentPoolPoolListItem] = []
        for grant in grants:
            passport = await self._passports.get_by_candidate_user_id(grant.candidate_user_id)
            if passport is None or passport.callsign is None or grant.responded_at is None:
                continue
            items.append(
                TalentPoolPoolListItem(
                    id=grant.id,
                    callsign=passport.callsign,
                    headline=passport.headline,
                    seniority=passport.seniority,
                    source_role_title=grant.source_role_title,
                    scope=TalentPoolScope(grant.scope),
                    granted_at=grant.responded_at,
                )
            )
        return items

    async def list_eligible_for_project(
        self, *, actor: User, project_id: uuid.UUID
    ) -> list[TalentPoolPoolListItem]:
        """Granted Talent Pool candidates eligible to be added to this project's pipeline --
        company_wide grants plus project_only grants scoped to this exact project. Powers "Add
        existing candidate" on a project's Candidates tab, the consent-gated replacement for
        manually creating a brand-new Candidate row."""
        project = await self._projects.get_by_id(project_id)
        if project is None or project.company_id != actor.company_id:
            raise ProjectNotFoundError()

        grants = await self._grants.list_eligible_for_job(
            company_id=actor.company_id, project_id=project_id
        )
        items: list[TalentPoolPoolListItem] = []
        for grant in grants:
            passport = await self._passports.get_by_candidate_user_id(grant.candidate_user_id)
            if passport is None or passport.callsign is None or grant.responded_at is None:
                continue
            items.append(
                TalentPoolPoolListItem(
                    id=grant.id,
                    callsign=passport.callsign,
                    headline=passport.headline,
                    seniority=passport.seniority,
                    source_role_title=grant.source_role_title,
                    scope=TalentPoolScope(grant.scope),
                    granted_at=grant.responded_at,
                )
            )
        return items

    # --- Candidate side: view and respond to requests --------------------------------------

    async def list_my_talent_pool_requests(
        self, *, candidate: CandidateUser
    ) -> list[CandidateTalentPoolRequestRead]:
        grants = await self._grants.list_by_candidate_id(candidate.id)
        items: list[CandidateTalentPoolRequestRead] = []
        for grant in grants:
            company = await self._session.get(Company, grant.company_id)
            items.append(
                CandidateTalentPoolRequestRead(
                    id=grant.id,
                    company_name=company.name if company else "Unknown company",
                    source_role_title=grant.source_role_title,
                    note=grant.note,
                    status=TalentPoolGrantStatus(grant.status),
                    scope=TalentPoolScope(grant.scope),
                    requested_at=grant.created_at,
                    responded_at=grant.responded_at,
                    review_date=grant.review_date,
                )
            )
        return items

    async def respond_to_talent_pool_request(
        self, *, candidate: CandidateUser, grant_id: uuid.UUID, body: TalentPoolDecision
    ) -> CandidateTalentPoolRequestRead:
        grant = await self._get_candidate_grant(candidate=candidate, grant_id=grant_id)
        if grant.status != TalentPoolGrantStatus.REQUESTED.value:
            raise TalentPoolRequestNotPendingError()

        review_date = date.today() + timedelta(days=_REVIEW_PERIOD_DAYS) if body.approve else None
        grant = await self._grants.respond(
            grant,
            approve=body.approve,
            scope=body.scope.value if body.approve else None,
            review_date=review_date,
        )
        await self._audit.record(
            company_id=grant.company_id,
            actor_user_id=None,
            action="talent_pool.granted" if body.approve else "talent_pool.declined",
            target_type="talent_pool_grant",
            target_id=grant.id,
            extra_data={"scope": grant.scope} if body.approve else {},
        )
        return await self._to_candidate_read(grant)

    async def withdraw_talent_pool_grant(
        self, *, candidate: CandidateUser, grant_id: uuid.UUID
    ) -> CandidateTalentPoolRequestRead:
        grant = await self._get_candidate_grant(candidate=candidate, grant_id=grant_id)
        if grant.status != TalentPoolGrantStatus.GRANTED.value:
            raise TalentPoolGrantNotActiveError()

        grant = await self._grants.withdraw(grant)
        await self._audit.record(
            company_id=grant.company_id,
            actor_user_id=None,
            action="talent_pool.withdrawn",
            target_type="talent_pool_grant",
            target_id=grant.id,
        )
        return await self._to_candidate_read(grant)

    # --- Shared helpers ----------------------------------------------------------------------

    async def _get_company_application(
        self, *, company_id: uuid.UUID, job_id: uuid.UUID, application_id: uuid.UUID
    ) -> ShadowApplication:
        job = await self._jobs.get_by_id(job_id)
        if job is None or job.company_id != company_id or job.deleted_at is not None:
            raise ShadowJobNotFoundError()
        application = await self._applications.get_by_id(application_id)
        if application is None or application.shadow_job_id != job_id:
            raise ShadowApplicationNotFoundError()
        return application

    async def _get_candidate_grant(
        self, *, candidate: CandidateUser, grant_id: uuid.UUID
    ) -> TalentPoolGrant:
        grant = await self._grants.get_by_id(grant_id)
        if grant is None or grant.candidate_user_id != candidate.id:
            raise TalentPoolRequestNotFoundError()
        return grant

    async def _to_candidate_read(self, grant: TalentPoolGrant) -> CandidateTalentPoolRequestRead:
        company = await self._session.get(Company, grant.company_id)
        return CandidateTalentPoolRequestRead(
            id=grant.id,
            company_name=company.name if company else "Unknown company",
            source_role_title=grant.source_role_title,
            note=grant.note,
            status=TalentPoolGrantStatus(grant.status),
            scope=TalentPoolScope(grant.scope),
            requested_at=grant.created_at,
            responded_at=grant.responded_at,
            review_date=grant.review_date,
        )


def _to_grant_read(grant: TalentPoolGrant) -> TalentPoolGrantRead:
    return TalentPoolGrantRead(
        id=grant.id,
        shadow_application_id=grant.source_shadow_application_id,
        source_role_title=grant.source_role_title,
        status=TalentPoolGrantStatus(grant.status),
        scope=TalentPoolScope(grant.scope),
        requested_at=grant.created_at,
        responded_at=grant.responded_at,
        review_date=grant.review_date,
        callsign=None,
    )
