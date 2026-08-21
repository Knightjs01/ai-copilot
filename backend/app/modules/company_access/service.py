import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth import security
from app.modules.auth.email import (
    EmailSender,
    build_info_requested_email,
    build_workspace_approved_email,
    build_workspace_rejected_email,
)
from app.modules.auth.exceptions import EmailAlreadyRegisteredError
from app.modules.auth.repository.users import UserRepository
from app.modules.auth.service.auth_service import AuthService
from app.modules.companies.domain_verification import extract_email_domain, is_verified_domain
from app.modules.companies.repository import CompanyRepository
from app.modules.company_access.exceptions import (
    AccessRequestNotFoundError,
    DuplicateRequestError,
    ExistingWorkspaceError,
    FreeEmailDomainError,
    RequestAlreadyReviewedError,
)
from app.modules.company_access.models import AccessRequestStatus
from app.modules.company_access.repository import CompanyAccessRequestRepository
from app.modules.company_access.schemas import CompanyAccessRequestCreate, CompanyAccessRequestRead
from app.modules.platform_admin.audit_service import PlatformAdminAuditService


class CompanyAccessRequestService:
    def __init__(self, session: AsyncSession, *, email_sender: EmailSender | None = None) -> None:
        self._session = session
        self._requests = CompanyAccessRequestRepository(session)
        self._users = UserRepository(session)
        self._companies = CompanyRepository(session)
        self._audit = PlatformAdminAuditService(session)
        self._email_sender = email_sender

    async def submit_request(self, body: CompanyAccessRequestCreate) -> CompanyAccessRequestRead:
        domain = extract_email_domain(body.work_email)
        if not is_verified_domain(domain):
            raise FreeEmailDomainError()

        if await self._companies.get_by_email_domain(domain) is not None:
            raise ExistingWorkspaceError()

        if await self._users.get_by_email(body.work_email) is not None:
            raise EmailAlreadyRegisteredError()

        existing_request = await self._requests.get_by_work_email(body.work_email)
        if (
            existing_request is not None
            and existing_request.status == AccessRequestStatus.PENDING.value
        ):
            raise DuplicateRequestError()

        request = await self._requests.create(
            full_name=body.full_name,
            job_title=body.job_title,
            company_name=body.company_name,
            work_email=body.work_email,
            hashed_password=security.hash_password(body.password),
        )
        return CompanyAccessRequestRead.model_validate(request)

    async def get_request(self, request_id: uuid.UUID) -> CompanyAccessRequestRead:
        request = await self._requests.get_by_id(request_id)
        if request is None:
            raise AccessRequestNotFoundError()
        return CompanyAccessRequestRead.model_validate(request)

    async def list_requests(self, *, status: str | None = None) -> list[CompanyAccessRequestRead]:
        requests = await self._requests.list_by_status(status)
        return [CompanyAccessRequestRead.model_validate(r) for r in requests]

    async def get_stats(self) -> dict[str, int]:
        return await self._requests.get_stats()

    async def approve_request(
        self, *, admin_id: uuid.UUID, request_id: uuid.UUID
    ) -> CompanyAccessRequestRead:
        request = await self._requests.get_by_id(request_id)
        if request is None:
            raise AccessRequestNotFoundError()
        if request.status != AccessRequestStatus.PENDING.value:
            raise RequestAlreadyReviewedError()

        # Race safety: re-check no company claimed this domain between submission and review.
        domain = extract_email_domain(request.work_email)
        if await self._companies.get_by_email_domain(domain) is not None:
            raise ExistingWorkspaceError()

        user = await AuthService(
            self._session, email_sender=self._email_sender
        ).provision_company_and_owner(
            company_name=request.company_name,
            owner_email=request.work_email,
            owner_full_name=request.full_name,
            owner_hashed_password=request.hashed_password,
        )

        request.status = AccessRequestStatus.APPROVED.value
        request.reviewed_by_admin_id = admin_id
        request.reviewed_at = datetime.now(timezone.utc)
        request.created_company_id = user.company_id
        await self._session.flush()

        await self._audit.record(
            admin_id=admin_id,
            action="access_request.approved",
            target_type="company_access_request",
            target_id=request.id,
            extra_data={"company_name": request.company_name, "work_email": request.work_email},
        )

        if self._email_sender is not None:
            subject, body = build_workspace_approved_email(company_name=request.company_name)
            await self._email_sender.send(to=request.work_email, subject=subject, body=body)

        return CompanyAccessRequestRead.model_validate(request)

    async def reject_request(
        self, *, admin_id: uuid.UUID, request_id: uuid.UUID, reason: str | None
    ) -> CompanyAccessRequestRead:
        request = await self._requests.get_by_id(request_id)
        if request is None:
            raise AccessRequestNotFoundError()
        if request.status != AccessRequestStatus.PENDING.value:
            raise RequestAlreadyReviewedError()

        request.status = AccessRequestStatus.REJECTED.value
        request.reviewed_by_admin_id = admin_id
        request.reviewed_at = datetime.now(timezone.utc)
        request.rejection_reason = reason
        await self._session.flush()

        await self._audit.record(
            admin_id=admin_id,
            action="access_request.rejected",
            target_type="company_access_request",
            target_id=request.id,
            extra_data={"company_name": request.company_name, "reason": reason},
        )

        if self._email_sender is not None:
            subject, body = build_workspace_rejected_email(
                company_name=request.company_name, reason=reason
            )
            await self._email_sender.send(to=request.work_email, subject=subject, body=body)

        return CompanyAccessRequestRead.model_validate(request)

    async def request_info(
        self, *, admin_id: uuid.UUID, request_id: uuid.UUID, message: str
    ) -> CompanyAccessRequestRead:
        """A message, not a state transition -- the request stays pending, still reviewable via
        approve/reject afterward."""

        request = await self._requests.get_by_id(request_id)
        if request is None:
            raise AccessRequestNotFoundError()
        if request.status != AccessRequestStatus.PENDING.value:
            raise RequestAlreadyReviewedError()

        await self._audit.record(
            admin_id=admin_id,
            action="access_request.info_requested",
            target_type="company_access_request",
            target_id=request.id,
            extra_data={"company_name": request.company_name, "message": message},
        )

        if self._email_sender is not None:
            subject, body = build_info_requested_email(
                company_name=request.company_name, message=message
            )
            await self._email_sender.send(to=request.work_email, subject=subject, body=body)

        return CompanyAccessRequestRead.model_validate(request)
