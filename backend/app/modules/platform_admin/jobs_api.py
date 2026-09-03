import uuid

from fastapi import APIRouter, Depends, Query
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
from app.modules.platform_admin.schemas import (
    AdminShadowJobDetail,
    AdminShadowJobRead,
    RejectShadowJobRequest,
)
from app.modules.shadow_jobs.models import ShadowJob
from app.modules.shadow_jobs.schemas import ShadowJobRead
from app.modules.shadow_jobs.service import ShadowJobService

router = APIRouter(prefix="/platform-admin/jobs", tags=["platform-admin"])


async def _to_admin_read(
    session: AsyncSession, service: ShadowJobService, job: ShadowJob
) -> AdminShadowJobRead:
    company = await CompanyRepository(session).get_by_id(job.company_id)
    company_name = company.name if company is not None else "Unknown company"
    read_model = ShadowJobRead.model_validate(job)
    read_model.applicant_count = await service.get_applicant_count(job.id)
    return AdminShadowJobRead(**read_model.model_dump(), company_name=company_name)


@router.get("", response_model=list[AdminShadowJobRead])
async def list_jobs(
    status_filter: str | None = Query(default=None, alias="status"),
    company_id: uuid.UUID | None = Query(default=None),
    _: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.JOBS_VIEW)
    ),
    session: AsyncSession = Depends(get_db),
) -> list[AdminShadowJobRead]:
    service = ShadowJobService(session)
    jobs = await service.list_admin_jobs(status=status_filter, company_id=company_id)
    return [await _to_admin_read(session, service, job) for job in jobs]


@router.get("/{job_id}", response_model=AdminShadowJobDetail)
async def get_job_detail(
    job_id: uuid.UUID,
    _: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.JOBS_VIEW)
    ),
    session: AsyncSession = Depends(get_db),
) -> AdminShadowJobDetail:
    service = ShadowJobService(session)
    job = await service.get_job_any_company(job_id)
    company = await CompanyRepository(session).get_by_id(job.company_id)
    match_count, interview_count, job_intelligence = await service.get_admin_job_metrics(job)
    read_model = ShadowJobRead.model_validate(job)
    read_model.applicant_count = await service.get_applicant_count(job.id)
    return AdminShadowJobDetail(
        **read_model.model_dump(),
        company_name=company.name if company is not None else "Unknown company",
        match_count=match_count,
        interview_count=interview_count,
        job_intelligence=job_intelligence,
    )


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
    return await _to_admin_read(session, service, job)


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
    return await _to_admin_read(session, service, job)
