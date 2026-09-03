import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.models import Company, CompanyProfileStatus
from app.modules.companies.repository import CompanyRepository
from app.modules.company_access.models import AccessRequestStatus, CompanyAccessRequest
from app.modules.company_access.repository import CompanyAccessRequestRepository
from app.modules.platform_admin.permissions import PlatformAdminPermissions
from app.modules.shadow_jobs.models import ShadowJob, ShadowJobStatus
from app.modules.shadow_jobs.repository import ShadowJobRepository

_STALE_AFTER = timedelta(hours=48)

ActionQueueItemType = Literal["access_request", "job_review", "profile_review"]


class ActionQueueItem(BaseModel):
    id: uuid.UUID
    type: ActionQueueItemType
    title: str
    subtitle: str
    company_name: str
    created_at: datetime
    priority: Literal["high", "normal"]
    url: str


def _priority(created_at: datetime) -> Literal["high", "normal"]:
    reference = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
    return "high" if datetime.now(timezone.utc) - reference > _STALE_AFTER else "normal"


def _access_request_item(request: CompanyAccessRequest) -> ActionQueueItem:
    return ActionQueueItem(
        id=request.id,
        type="access_request",
        title=request.company_name,
        subtitle=f"{request.full_name} requested access",
        company_name=request.company_name,
        created_at=request.created_at,
        priority=_priority(request.created_at),
        url="/platform-admin/requests",
    )


def _job_review_item(job: ShadowJob, *, company_name: str) -> ActionQueueItem:
    return ActionQueueItem(
        id=job.id,
        type="job_review",
        title=job.title,
        subtitle=f"{company_name} submitted this role for review",
        company_name=company_name,
        created_at=job.created_at,
        priority=_priority(job.created_at),
        url="/platform-admin/jobs",
    )


def _profile_review_item(company: Company) -> ActionQueueItem:
    return ActionQueueItem(
        id=company.id,
        type="profile_review",
        title=company.name,
        subtitle=f"{company.name} submitted their profile for review",
        company_name=company.name,
        created_at=company.created_at,
        priority=_priority(company.created_at),
        url="/platform-admin/companies",
    )


class ActionQueueService:
    """Pure aggregation over real, already-existing review queues -- no new tables. Mirrors
    dashboard.service.DashboardService's "fan out to other modules' repositories, assemble one
    flat list" shape. Each source is included only when the caller holds the permission that
    already gates its own page, so an admin without jobs.view never sees job-review items even
    though the endpoint itself has no single fixed permission requirement."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._access_requests = CompanyAccessRequestRepository(session)
        self._jobs = ShadowJobRepository(session)
        self._companies = CompanyRepository(session)

    async def list_items(self, *, permissions: set[str]) -> list[ActionQueueItem]:
        items: list[ActionQueueItem] = []

        if PlatformAdminPermissions.COMPANIES_VIEW in permissions:
            pending_requests = await self._access_requests.list_by_status(
                AccessRequestStatus.PENDING.value
            )
            items.extend(_access_request_item(request) for request in pending_requests)

            pending_profiles = await self._companies.list_all(
                profile_status=CompanyProfileStatus.PENDING_REVIEW.value
            )
            items.extend(_profile_review_item(company) for company in pending_profiles)

        if PlatformAdminPermissions.JOBS_VIEW in permissions:
            pending_jobs = await self._jobs.list_by_status(ShadowJobStatus.PENDING_REVIEW.value)
            for job in pending_jobs:
                company = await self._companies.get_by_id(job.company_id)
                items.append(
                    _job_review_item(job, company_name=company.name if company else "Unknown company")
                )

        items.sort(key=lambda item: (item.priority != "high", item.created_at))
        return items
