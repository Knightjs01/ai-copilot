import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import limiter
from app.db.session import get_db
from app.modules.auth.dependencies import get_email_sender
from app.modules.auth.email import EmailSender
from app.modules.companies.service import CompanyService
from app.modules.company_access.schemas import (
    AccessRequestStatsRead,
    CompanyAccessRequestCreate,
    CompanyAccessRequestRead,
    RejectAccessRequestBody,
    RequestInfoBody,
)
from app.modules.company_access.service import CompanyAccessRequestService
from app.modules.phantom_passport.models import VerificationStatus
from app.modules.phantom_passport.repository import PhantomPassportRepository
from app.modules.platform_admin.audit_service import PlatformAdminAuditService
from app.modules.platform_admin.dependencies import (
    PlatformAdminContext,
    require_platform_admin_permission,
)
from app.modules.platform_admin.permissions import PlatformAdminPermissions
from app.modules.platform_admin.schemas import PlatformAdminAuditLogRead
from app.modules.shadow_jobs.models import ShadowJobStatus
from app.modules.shadow_jobs.repository import ShadowApplicationRepository, ShadowJobRepository

router = APIRouter(prefix="/company-access", tags=["company-access"])


@router.post(
    "/requests", response_model=CompanyAccessRequestRead, status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/minute")
async def submit_access_request(
    request: Request,
    body: CompanyAccessRequestCreate,
    session: AsyncSession = Depends(get_db),
) -> CompanyAccessRequestRead:
    return await CompanyAccessRequestService(session).submit_request(body)


@router.get("/requests", response_model=list[CompanyAccessRequestRead])
async def list_access_requests(
    status_filter: str | None = Query(default="pending", alias="status"),
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_VIEW)
    ),
    session: AsyncSession = Depends(get_db),
) -> list[CompanyAccessRequestRead]:
    return await CompanyAccessRequestService(session).list_requests(status=status_filter)


@router.get("/requests/{request_id}", response_model=CompanyAccessRequestRead)
async def get_access_request(
    request_id: uuid.UUID,
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_VIEW)
    ),
    session: AsyncSession = Depends(get_db),
) -> CompanyAccessRequestRead:
    return await CompanyAccessRequestService(session).get_request(request_id)


@router.post("/requests/{request_id}/approve", response_model=CompanyAccessRequestRead)
async def approve_access_request(
    request_id: uuid.UUID,
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_REVIEW)
    ),
    session: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> CompanyAccessRequestRead:
    return await CompanyAccessRequestService(session, email_sender=email_sender).approve_request(
        admin_id=admin.id, request_id=request_id
    )


@router.post("/requests/{request_id}/reject", response_model=CompanyAccessRequestRead)
async def reject_access_request(
    request_id: uuid.UUID,
    body: RejectAccessRequestBody = RejectAccessRequestBody(),
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_REVIEW)
    ),
    session: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> CompanyAccessRequestRead:
    return await CompanyAccessRequestService(session, email_sender=email_sender).reject_request(
        admin_id=admin.id, request_id=request_id, reason=body.reason
    )


@router.post("/requests/{request_id}/request-info", response_model=CompanyAccessRequestRead)
async def request_more_info(
    request_id: uuid.UUID,
    body: RequestInfoBody,
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_REVIEW)
    ),
    session: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> CompanyAccessRequestRead:
    return await CompanyAccessRequestService(session, email_sender=email_sender).request_info(
        admin_id=admin.id, request_id=request_id, message=body.message
    )


@router.get("/stats", response_model=AccessRequestStatsRead)
async def get_stats(
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_VIEW)
    ),
    session: AsyncSession = Depends(get_db),
) -> AccessRequestStatsRead:
    request_stats = await CompanyAccessRequestService(session).get_stats()
    company_stats = await CompanyService(session).get_status_counts()
    active_role_count = await ShadowJobRepository(session).count_by_status(
        ShadowJobStatus.PUBLISHED.value
    )
    verified_candidate_count = await PhantomPassportRepository(session).count_by_verification_status(
        VerificationStatus.VERIFIED.value
    )
    application_count = await ShadowApplicationRepository(session).count_all()
    return AccessRequestStatsRead(
        **request_stats,
        **company_stats,
        active_role_count=active_role_count,
        verified_candidate_count=verified_candidate_count,
        application_count=application_count,
    )


@router.get("/audit-log", response_model=list[PlatformAdminAuditLogRead])
async def get_audit_log(
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.AUDIT_VIEW)
    ),
    session: AsyncSession = Depends(get_db),
) -> list[PlatformAdminAuditLogRead]:
    entries = await PlatformAdminAuditService(session).list_recent()
    return [PlatformAdminAuditLogRead.model_validate(e) for e in entries]
