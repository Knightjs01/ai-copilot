import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.dependencies import get_email_sender
from app.modules.auth.email import EmailSender
from app.modules.companies.repository import CompanyRepository
from app.modules.job_alerts.service import JobAlertService
from app.modules.platform_admin.audit_service import PlatformAdminAuditService
from app.modules.platform_admin.dependencies import (
    PlatformAdminContext,
    require_platform_admin_permission,
)
from app.modules.platform_admin.permissions import PlatformAdminPermissions
from app.modules.platform_admin.schemas import AdminShadowJobRead, RejectShadowJobRequest
from app.modules.shadow_jobs.models import ShadowJob
from app.modules.shadow_jobs.schemas import ShadowJobRead
from app.modules.shadow_jobs.service import ShadowJobService

router = APIRouter(prefix="/platform-admin/jobs", tags=["platform-admin"])


async def _to_admin_read(session: AsyncSession, job: ShadowJob) -> AdminShadowJobRead:
    company = await CompanyRepository(session).get_by_id(job.company_id)
    company_name = company.name if company is not None else "Unknown company"
    return AdminShadowJobRead(
        **ShadowJobRead.model_validate(job).model_dump(), company_name=company_name
    )


@router.get("/pending-review", response_model=list[AdminShadowJobRead])
async def list_pending_review(
    _: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.JOBS_VIEW)
    ),
    session: AsyncSession = Depends(get_db),
) -> list[AdminShadowJobRead]:
    jobs = await ShadowJobService(session).list_pending_review()
    return [await _to_admin_read(session, job) for job in jobs]


@router.post("/{job_id}/approve", response_model=AdminShadowJobRead)
async def approve_job(
    job_id: uuid.UUID,
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.JOBS_REVIEW)
    ),
    session: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> AdminShadowJobRead:
    service = ShadowJobService(session)
    job = await service.approve_pending_job(job_id=job_id)
    # The real "goes public" moment -- alert emails only ever fire once a job is genuinely
    # approved, never at the recruiter's own submit-for-review action.
    await JobAlertService(session, email_sender=email_sender).notify_matching_alerts(job)
    await PlatformAdminAuditService(session).record(
        admin_id=admin.id,
        action="shadow_job.approved",
        target_type="shadow_job",
        target_id=job.id,
    )
    return await _to_admin_read(session, job)


@router.post("/{job_id}/reject", response_model=AdminShadowJobRead)
async def reject_job(
    job_id: uuid.UUID,
    body: RejectShadowJobRequest,
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.JOBS_REVIEW)
    ),
    session: AsyncSession = Depends(get_db),
) -> AdminShadowJobRead:
    service = ShadowJobService(session)
    job = await service.reject_pending_job(job_id=job_id)
    await PlatformAdminAuditService(session).record(
        admin_id=admin.id,
        action="shadow_job.rejected",
        target_type="shadow_job",
        target_id=job.id,
        extra_data={"reason": body.reason} if body.reason else {},
    )
    return await _to_admin_read(session, job)
