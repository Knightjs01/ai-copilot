import uuid
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import AuditService
from app.modules.auth.models import User
from app.modules.candidate_auth.models import CandidateUser
from app.modules.companies.models import Company
from app.modules.phantom_passport.repository import PhantomPassportRepository
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
    TalentPoolDecision,
    TalentPoolGrantRead,
    TalentPoolPoolListItem,
    TalentPoolRequestCreate,
)

_REVIEW_PERIOD_DAYS = 365

_ELIGIBLE_APPLICATION_STATUSES = {
    ShadowApplicationStatus.DECLINED.value,
    ShadowApplicationStatus.WITHDRAWN.value,
}


class TalentPoolService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._grants = TalentPoolGrantRepository(session)
        self._applications = ShadowApplicationRepository(session)
        self._jobs = ShadowJobRepository(session)
        self._passports = PhantomPassportRepository(session)
        self._audit = AuditService(session)

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
        return _to_grant_read(grant)

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
