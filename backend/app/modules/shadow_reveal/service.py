import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.disclosure import SHADOW_TIER_FIELDS, DisclosureLevel, ShadowField
from app.modules.audit.service import AuditService
from app.modules.auth import security
from app.modules.auth.models import User
from app.modules.candidate_auth.models import CandidateUser
from app.modules.candidate_auth.repository import CandidateUserRepository
from app.modules.companies.models import Company
from app.modules.phantom_passport.exceptions import PassportNotFoundError
from app.modules.phantom_passport.repository import (
    PassportCareerEntryRepository,
    PassportPersonalInfoRepository,
    PhantomPassportRepository,
)
from app.modules.shadow_jobs.exceptions import (
    ShadowApplicationNotFoundError,
    ShadowJobNotFoundError,
)
from app.modules.shadow_jobs.models import ShadowApplication, ShadowApplicationStatus
from app.modules.shadow_jobs.repository import ShadowApplicationRepository, ShadowJobRepository
from app.modules.shadow_reveal.exceptions import (
    DuplicateRevealRequestError,
    InvalidDisclosedFieldsError,
    RevealNotApprovedError,
    RevealRequestNotFoundError,
    RevealRequestNotPendingError,
)
from app.modules.shadow_reveal.models import RevealRequestStatus, ShadowRevealRequest
from app.modules.shadow_reveal.repository import ShadowRevealRequestRepository
from app.modules.shadow_reveal.schemas import (
    CandidateRevealRequestRead,
    RevealDecision,
    RevealedCareerEntry,
    RevealedIdentity,
    RevealRequestCreate,
    RevealRequestRead,
)


class ShadowRevealService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._requests = ShadowRevealRequestRepository(session)
        self._applications = ShadowApplicationRepository(session)
        self._jobs = ShadowJobRepository(session)
        self._passports = PhantomPassportRepository(session)
        self._personal_info = PassportPersonalInfoRepository(session)
        self._career_entries = PassportCareerEntryRepository(session)
        self._candidate_users = CandidateUserRepository(session)
        self._audit = AuditService(session)

    # --- Company side: request a reveal ---------------------------------------------------

    async def request_reveal(
        self,
        *,
        actor: User,
        job_id: uuid.UUID,
        application_id: uuid.UUID,
        body: RevealRequestCreate,
    ) -> RevealRequestRead:
        application = await self._get_company_application(
            company_id=actor.company_id, job_id=job_id, application_id=application_id
        )
        existing = await self._requests.get_by_application_id(application.id)
        if existing is not None:
            raise DuplicateRevealRequestError()

        request = await self._requests.create(
            company_id=actor.company_id,
            shadow_application_id=application.id,
            requested_by_user_id=actor.id,
            reason=body.reason,
        )
        await self._applications.update_status(
            application, status=ShadowApplicationStatus.REVEAL_REQUESTED.value
        )
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="shadow_reveal.requested",
            target_type="shadow_application",
            target_id=application.id,
            extra_data={"reveal_request_id": str(request.id)},
        )
        return _to_request_read(request, callsign=application.callsign)

    async def get_revealed_identity(
        self, *, company_id: uuid.UUID, job_id: uuid.UUID, application_id: uuid.UUID
    ) -> RevealedIdentity:
        application = await self._get_company_application(
            company_id=company_id, job_id=job_id, application_id=application_id
        )
        request = await self._requests.get_by_application_id(application.id)
        if request is None or request.status != RevealRequestStatus.APPROVED.value:
            raise RevealNotApprovedError()

        return await self._build_disclosure(application=application, request=request)

    # --- Candidate side: view and respond to a pending request ----------------------------

    async def get_my_reveal_request(
        self, *, candidate: CandidateUser, application_id: uuid.UUID
    ) -> CandidateRevealRequestRead:
        application = await self._get_candidate_application(
            candidate=candidate, application_id=application_id
        )
        request = await self._requests.get_by_application_id(application.id)
        if request is None:
            raise RevealRequestNotFoundError()

        job = await self._jobs.get_by_id(application.shadow_job_id)
        if job is None:
            raise ShadowJobNotFoundError()
        company = await self._session.get(Company, job.company_id)

        return CandidateRevealRequestRead(
            id=request.id,
            shadow_application_id=application.id,
            job_title=job.title,
            company_name=company.name if company else "Unknown company",
            reason=request.reason,
            status=RevealRequestStatus(request.status),
            requested_at=request.created_at,
        )

    async def respond_to_reveal_request(
        self, *, candidate: CandidateUser, application_id: uuid.UUID, body: RevealDecision
    ) -> CandidateRevealRequestRead:
        application = await self._get_candidate_application(
            candidate=candidate, application_id=application_id
        )
        request = await self._requests.get_by_application_id(application.id)
        if request is None:
            raise RevealRequestNotFoundError()
        if request.status != RevealRequestStatus.PENDING.value:
            raise RevealRequestNotPendingError()

        if body.disclosed_fields is not None and not body.disclosed_fields:
            raise InvalidDisclosedFieldsError()

        stored_level = DisclosureLevel.CUSTOM if body.disclosed_fields else body.disclosure_level
        request = await self._requests.respond(
            request,
            approve=body.approve,
            disclosure_level=stored_level.value,
            disclosed_fields=(
                [f.value for f in body.disclosed_fields] if body.disclosed_fields else None
            ),
        )
        await self._applications.update_status(
            application,
            status=(
                ShadowApplicationStatus.REVEALED.value
                if body.approve
                else ShadowApplicationStatus.DECLINED.value
            ),
        )
        await self._audit.record(
            company_id=application.company_id,
            actor_user_id=None,
            action="shadow_reveal.approved" if body.approve else "shadow_reveal.declined",
            target_type="shadow_application",
            target_id=application.id,
            extra_data={
                "reveal_request_id": str(request.id),
                **({"disclosure_level": stored_level.value} if body.approve else {}),
            },
        )

        job = await self._jobs.get_by_id(application.shadow_job_id)
        company = await self._session.get(Company, job.company_id) if job else None
        return CandidateRevealRequestRead(
            id=request.id,
            shadow_application_id=application.id,
            job_title=job.title if job else "Unknown role",
            company_name=company.name if company else "Unknown company",
            reason=request.reason,
            status=RevealRequestStatus(request.status),
            requested_at=request.created_at,
        )

    # --- Shared helpers ---------------------------------------------------------------------

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

    async def _get_candidate_application(
        self, *, candidate: CandidateUser, application_id: uuid.UUID
    ) -> ShadowApplication:
        application = await self._applications.get_by_id(application_id)
        if application is None or application.candidate_user_id != candidate.id:
            raise ShadowApplicationNotFoundError()
        return application

    async def _build_disclosure(
        self, *, application: ShadowApplication, request: ShadowRevealRequest
    ) -> RevealedIdentity:
        passport = await self._passports.get_by_candidate_user_id(application.candidate_user_id)
        if passport is None:
            raise PassportNotFoundError()
        personal_info = await self._personal_info.get_by_passport_id(passport.id)
        if personal_info is None:
            raise PassportNotFoundError("Passport is missing its personal information record")
        candidate_user = await self._candidate_users.get_by_id(application.candidate_user_id)
        if candidate_user is None:
            raise ShadowApplicationNotFoundError()

        # request.disclosure_level is only ever unset for a pre-migration-backfill row that was
        # approved before this column existed — default to FULL so old approvals keep behaving
        # exactly as they did before disclosure levels existed, rather than silently narrowing.
        disclosure_level = DisclosureLevel(request.disclosure_level or DisclosureLevel.FULL.value)
        if request.disclosed_fields:
            effective_fields = {ShadowField(f) for f in request.disclosed_fields}
        else:
            effective_fields = set(
                SHADOW_TIER_FIELDS.get(disclosure_level, SHADOW_TIER_FIELDS[DisclosureLevel.FULL])
            )

        career_entries = (
            [
                RevealedCareerEntry(
                    title=entry.title,
                    company_name=security.decrypt_secret(entry.company_name_encrypted),
                    is_current=entry.is_current,
                )
                for entry in await self._career_entries.list_by_passport_id(passport.id)
            ]
            if ShadowField.CAREER_HISTORY in effective_fields
            else []
        )

        return RevealedIdentity(
            application_id=application.id,
            disclosure_level=disclosure_level,
            disclosed_fields=sorted(effective_fields, key=lambda f: f.value),
            callsign=application.callsign,
            full_name=(
                security.decrypt_secret(personal_info.legal_name_encrypted)
                if ShadowField.FULL_NAME in effective_fields
                else None
            ),
            email=candidate_user.email if ShadowField.EMAIL in effective_fields else None,
            phone=(
                security.decrypt_secret(personal_info.phone_encrypted)
                if ShadowField.PHONE in effective_fields and personal_info.phone_encrypted
                else None
            ),
            career_entries=career_entries,
            revealed_at=request.responded_at or application.updated_at,
        )


def _to_request_read(request: ShadowRevealRequest, *, callsign: str) -> RevealRequestRead:
    return RevealRequestRead(
        id=request.id,
        shadow_application_id=request.shadow_application_id,
        callsign=callsign,
        reason=request.reason,
        status=RevealRequestStatus(request.status),
        requested_at=request.created_at,
        responded_at=request.responded_at,
    )
