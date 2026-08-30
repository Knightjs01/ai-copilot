import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.audit.service import AuditService
from app.modules.auth.email import (
    EmailSender,
    build_introduction_request_email,
    build_introduction_response_email,
)
from app.modules.auth.models import User
from app.modules.candidate_auth.models import CandidateUser
from app.modules.candidate_auth.repository import CandidateUserRepository
from app.modules.companies.models import Company
from app.modules.phantom_passport.models import PhantomPassport
from app.modules.phantom_passport.repository import PhantomPassportRepository
from app.modules.shadow_introduction.exceptions import (
    CandidateNoLongerDiscoverableError,
    DuplicateIntroductionRequestError,
    IntroductionRequestNotFoundError,
    IntroductionRequestNotPendingError,
)
from app.modules.shadow_introduction.models import IntroductionRequest, IntroductionRequestStatus
from app.modules.shadow_introduction.repository import IntroductionRequestRepository
from app.modules.shadow_introduction.schemas import (
    CandidateIntroductionRequestRead,
    IntroductionDecision,
    IntroductionRequestCreate,
    IntroductionRequestRead,
)
from app.modules.shadow_jobs.exceptions import ShadowJobNotFoundError
from app.modules.shadow_jobs.repository import ShadowJobRepository
from app.modules.shadow_jobs.service import ShadowJobService

logger = logging.getLogger("app.shadow_introduction.service")


def _is_discoverable(passport: PhantomPassport) -> bool:
    """Same eligibility gate as talent_pool.service._is_discoverable / PhantomPassportRepository.
    list_discoverable_candidates -- re-checked server-side, never trusted from a possibly-stale
    client-held search result."""
    return (
        passport.visibility != "private"
        and passport.career_intent != "not_looking"
        and passport.current_version_id is not None
        and passport.deleted_at is None
    )


class IntroductionService:
    def __init__(self, session: AsyncSession, *, email_sender: EmailSender | None = None) -> None:
        self._session = session
        self._requests = IntroductionRequestRepository(session)
        self._jobs = ShadowJobRepository(session)
        self._passports = PhantomPassportRepository(session)
        self._candidate_users = CandidateUserRepository(session)
        self._audit = AuditService(session)
        self._email_sender = email_sender
        self._settings = get_settings()

    # --- Company side: request an introduction ----------------------------------------------

    async def request_introduction(
        self, *, actor: User, job_id: uuid.UUID, callsign: str, body: IntroductionRequestCreate
    ) -> IntroductionRequestRead:
        job = await self._jobs.get_by_id(job_id)
        if job is None or job.company_id != actor.company_id or job.deleted_at is not None:
            raise ShadowJobNotFoundError()

        passport = await self._passports.get_by_callsign(callsign)
        if passport is None or not _is_discoverable(passport):
            raise CandidateNoLongerDiscoverableError()

        existing = await self._requests.get_active_by_triple(
            candidate_user_id=passport.candidate_user_id,
            company_id=actor.company_id,
            shadow_job_id=job_id,
        )
        if existing is not None:
            raise DuplicateIntroductionRequestError()

        request = await self._requests.create(
            company_id=actor.company_id,
            candidate_user_id=passport.candidate_user_id,
            shadow_job_id=job_id,
            requested_by_user_id=actor.id,
            message=body.message,
        )
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="shadow_introduction.requested",
            target_type="phantom_passport",
            target_id=passport.id,
            extra_data={"introduction_request_id": str(request.id), "shadow_job_id": str(job_id)},
        )
        await self._notify_candidate_of_request(
            candidate_user_id=passport.candidate_user_id,
            company_id=actor.company_id,
            role_title=job.title,
        )
        return _to_company_read(request, callsign=passport.callsign or "Unknown")

    async def list_company_introduction_requests(
        self, *, actor: User, job_id: uuid.UUID
    ) -> list[IntroductionRequestRead]:
        job = await self._jobs.get_by_id(job_id)
        if job is None or job.company_id != actor.company_id or job.deleted_at is not None:
            raise ShadowJobNotFoundError()

        requests = await self._requests.list_by_company_and_job(
            company_id=actor.company_id, shadow_job_id=job_id
        )
        items: list[IntroductionRequestRead] = []
        for request in requests:
            passport = await self._passports.get_by_candidate_user_id(request.candidate_user_id)
            items.append(_to_company_read(request, callsign=(passport.callsign if passport else None) or "Unknown"))
        return items

    async def _notify_candidate_of_request(
        self, *, candidate_user_id: uuid.UUID, company_id: uuid.UUID, role_title: str
    ) -> None:
        if self._email_sender is None:
            return
        candidate = await self._candidate_users.get_by_id(candidate_user_id)
        company = await self._session.get(Company, company_id)
        if candidate is None or company is None:
            return
        requests_url = f"{self._settings.frontend_base_url}/shadow/introductions"
        subject, body = build_introduction_request_email(
            company_name=company.name, role_title=role_title, requests_url=requests_url
        )
        try:
            await self._email_sender.send(to=candidate.email, subject=subject, body=body)
        except Exception:
            # A send failure must never fail the request it's riding along with.
            logger.exception(
                "Failed to send introduction request email to candidate %s", candidate_user_id
            )

    async def _notify_company_of_response(
        self, *, request: IntroductionRequest, approved: bool, callsign: str
    ) -> None:
        if self._email_sender is None:
            return
        requester = await self._session.get(User, request.requested_by_user_id)
        if requester is None:
            return
        applicant_url = f"{self._settings.frontend_base_url}/shadow-jobs"
        subject, body = build_introduction_response_email(
            callsign=callsign, approved=approved, applicant_url=applicant_url
        )
        try:
            await self._email_sender.send(to=requester.email, subject=subject, body=body)
        except Exception:
            logger.exception(
                "Failed to send introduction response email for request %s", request.id
            )

    # --- Candidate side: view and respond to requests ----------------------------------------

    async def list_my_introduction_requests(
        self, *, candidate: CandidateUser
    ) -> list[CandidateIntroductionRequestRead]:
        requests = await self._requests.list_by_candidate_id(candidate.id)
        items: list[CandidateIntroductionRequestRead] = []
        for request in requests:
            items.append(await self._to_candidate_read(request))
        return items

    async def respond_to_introduction_request(
        self, *, candidate: CandidateUser, request_id: uuid.UUID, body: IntroductionDecision
    ) -> CandidateIntroductionRequestRead:
        request = await self._get_candidate_request(candidate=candidate, request_id=request_id)
        if request.status != IntroductionRequestStatus.PENDING.value:
            raise IntroductionRequestNotPendingError()

        passport = await self._passports.get_by_candidate_user_id(candidate.id)
        callsign = (passport.callsign if passport else None) or "Unknown"

        if not body.approve:
            request = await self._requests.respond(request, approve=False)
            await self._audit.record(
                company_id=request.company_id,
                actor_user_id=None,
                action="shadow_introduction.declined",
                target_type="shadow_introduction_request",
                target_id=request.id,
            )
            await self._notify_company_of_response(
                request=request, approved=False, callsign=callsign
            )
            return await self._to_candidate_read(request)

        # Reuses ShadowJobService.create_application_from_introduction -- a real ShadowApplication
        # gets created (or an existing one reused), which is what makes the existing Messages
        # system and Phase 1's RelationshipStatus computation work here with zero changes.
        application = await ShadowJobService(self._session).create_application_from_introduction(
            candidate=candidate, job_id=request.shadow_job_id
        )
        request = await self._requests.respond(
            request, approve=True, resulting_application_id=application.id
        )
        await self._audit.record(
            company_id=request.company_id,
            actor_user_id=None,
            action="shadow_introduction.accepted",
            target_type="shadow_application",
            target_id=application.id,
            extra_data={"introduction_request_id": str(request.id)},
        )
        await self._notify_company_of_response(request=request, approved=True, callsign=callsign)
        return await self._to_candidate_read(request)

    # --- Shared helpers ------------------------------------------------------------------------

    async def _get_candidate_request(
        self, *, candidate: CandidateUser, request_id: uuid.UUID
    ) -> IntroductionRequest:
        request = await self._requests.get_by_id(request_id)
        if request is None or request.candidate_user_id != candidate.id:
            raise IntroductionRequestNotFoundError()
        return request

    async def _to_candidate_read(
        self, request: IntroductionRequest
    ) -> CandidateIntroductionRequestRead:
        company = await self._session.get(Company, request.company_id)
        job = await self._jobs.get_by_id(request.shadow_job_id)
        return CandidateIntroductionRequestRead(
            id=request.id,
            company_name=company.name if company else "Unknown company",
            job_title=job.title if job else "Unknown role",
            message=request.message,
            status=IntroductionRequestStatus(request.status),
            requested_at=request.created_at,
            responded_at=request.responded_at,
            resulting_application_id=request.resulting_application_id,
        )


def _to_company_read(request: IntroductionRequest, *, callsign: str) -> IntroductionRequestRead:
    return IntroductionRequestRead(
        id=request.id,
        callsign=callsign,
        shadow_job_id=request.shadow_job_id,
        message=request.message,
        status=IntroductionRequestStatus(request.status),
        requested_at=request.created_at,
        responded_at=request.responded_at,
        resulting_application_id=request.resulting_application_id,
    )
