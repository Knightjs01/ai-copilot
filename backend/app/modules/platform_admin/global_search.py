import uuid
from typing import Literal

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.models import Company
from app.modules.companies.repository import CompanyRepository
from app.modules.phantom_passport.models import PhantomPassport
from app.modules.phantom_passport.repository import PhantomPassportRepository
from app.modules.platform_admin.permissions import PlatformAdminPermissions
from app.modules.shadow_jobs.models import ShadowJob
from app.modules.shadow_jobs.repository import ShadowJobRepository

_RESULTS_PER_TYPE = 5

GlobalSearchResultType = Literal["company", "job", "candidate"]


class GlobalSearchResultItem(BaseModel):
    id: uuid.UUID
    type: GlobalSearchResultType
    title: str
    subtitle: str
    url: str


def _company_item(company: Company) -> GlobalSearchResultItem:
    return GlobalSearchResultItem(
        id=company.id,
        type="company",
        title=company.name,
        subtitle=company.email_domain,
        url=f"/platform-admin/companies/{company.id}",
    )


def _job_item(job: ShadowJob) -> GlobalSearchResultItem:
    return GlobalSearchResultItem(
        id=job.id,
        type="job",
        title=job.title,
        subtitle=job.status,
        url=f"/platform-admin/jobs/{job.id}",
    )


def _candidate_item(passport: PhantomPassport) -> GlobalSearchResultItem:
    return GlobalSearchResultItem(
        id=passport.id,
        type="candidate",
        title=passport.callsign or "Not yet approved",
        subtitle=passport.headline or passport.verification_status,
        url=f"/platform-admin/candidates/{passport.id}",
    )


class GlobalSearchService:
    """Pure aggregation over the three existing Command entities' own search() methods -- no new
    tables, no cross-type relevance ranking (each type keeps its own natural created_at-desc
    order; nothing here fabricates a merged relevance score across such different entity types).
    Mirrors ActionQueueService's own "each source included only when the caller holds the
    permission that already gates its own page" pattern -- there is no single fixed permission on
    the route this powers."""

    def __init__(self, session: AsyncSession) -> None:
        self._companies = CompanyRepository(session)
        self._jobs = ShadowJobRepository(session)
        self._candidates = PhantomPassportRepository(session)

    async def search(
        self, *, query: str, permissions: set[str]
    ) -> list[GlobalSearchResultItem]:
        results: list[GlobalSearchResultItem] = []

        if PlatformAdminPermissions.COMPANIES_VIEW in permissions:
            companies = await self._companies.list_all(search=query, limit=_RESULTS_PER_TYPE)
            results.extend(_company_item(company) for company in companies)

        if PlatformAdminPermissions.JOBS_VIEW in permissions:
            jobs = await self._jobs.list_all(search=query, limit=_RESULTS_PER_TYPE)
            results.extend(_job_item(job) for job in jobs)

        if PlatformAdminPermissions.CANDIDATES_VIEW in permissions:
            candidates = await self._candidates.list_all(search=query, limit=_RESULTS_PER_TYPE)
            results.extend(_candidate_item(passport) for passport in candidates)

        return results
