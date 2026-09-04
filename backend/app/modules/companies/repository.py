import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.models import Company, CompanyProfileVersion


class CompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        name: str,
        slug: str,
        email_domain: str,
        is_verified_domain: bool,
        commercial_plan_id: uuid.UUID | None = None,
    ) -> Company:
        company = Company(
            name=name,
            slug=slug,
            email_domain=email_domain,
            is_verified_domain=is_verified_domain,
            commercial_plan_id=commercial_plan_id,
        )
        self._session.add(company)
        await self._session.flush()
        return company

    async def get_by_id(self, company_id: uuid.UUID) -> Company | None:
        return await self._session.get(Company, company_id)

    async def get_by_slug(self, slug: str) -> Company | None:
        result = await self._session.execute(select(Company).where(Company.slug == slug))
        return result.scalar_one_or_none()

    async def get_by_email_domain(self, email_domain: str) -> Company | None:
        # .first(), not .scalar_one_or_none() -- there's no DB-level uniqueness constraint on
        # email_domain (see company_access/service.py's own "race safety" comment: the
        # check-then-create flow is only best-effort), so more than one row can legitimately
        # exist for a domain. Every caller only checks "is a company already using this domain",
        # not "give me the one true owner" -- .scalar_one_or_none() would raise
        # MultipleResultsFound in exactly the case this method exists to detect.
        result = await self._session.execute(
            select(Company).where(
                Company.email_domain == email_domain, Company.deleted_at.is_(None)
            )
        )
        return result.scalars().first()

    async def slug_exists(self, slug: str) -> bool:
        result = await self._session.execute(select(Company.id).where(Company.slug == slug))
        return result.scalar_one_or_none() is not None

    async def list_all(
        self,
        *,
        profile_status: str | None = None,
        search: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Company]:
        query = select(Company).where(Company.deleted_at.is_(None))
        if profile_status is not None:
            query = query.where(Company.profile_status == profile_status)
        if search:
            query = query.where(Company.name.ilike(f"%{search}%"))
        query = query.order_by(Company.created_at.desc())
        if limit is not None:
            query = query.limit(limit).offset(offset)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_all(
        self, *, profile_status: str | None = None, search: str | None = None
    ) -> int:
        query = select(func.count()).select_from(Company).where(Company.deleted_at.is_(None))
        if profile_status is not None:
            query = query.where(Company.profile_status == profile_status)
        if search:
            query = query.where(Company.name.ilike(f"%{search}%"))
        result = await self._session.execute(query)
        return result.scalar_one()

    async def get_status_counts(self) -> dict[str, int]:
        result = await self._session.execute(
            select(Company.status, func.count())
            .where(Company.deleted_at.is_(None))
            .group_by(Company.status)
        )
        return {status: count for status, count in result.all()}

    async def update(
        self,
        company: Company,
        *,
        description: str | None,
        culture: str | None,
        benefits: list[Any],
        size: str | None,
        industry: list[Any],
        hiring_process_overview: str | None,
        tagline: str | None,
        website: str | None,
        founded_year: int | None,
        headquarters: str | None,
        employee_count: int | None,
        values: list[Any],
        looking_for: list[Any],
        hiring_highlights: list[Any],
    ) -> Company:
        company.description = description
        company.culture = culture
        company.benefits = benefits
        company.size = size
        company.industry = industry
        company.hiring_process_overview = hiring_process_overview
        company.tagline = tagline
        company.website = website
        company.founded_year = founded_year
        company.headquarters = headquarters
        company.employee_count = employee_count
        company.values = values
        company.looking_for = looking_for
        company.hiring_highlights = hiring_highlights
        await self._session.flush()
        return company


class CompanyProfileVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        version_number: int,
        snapshot: dict[str, Any],
        approved_by_admin_id: uuid.UUID | None,
    ) -> CompanyProfileVersion:
        version = CompanyProfileVersion(
            company_id=company_id,
            version_number=version_number,
            snapshot=snapshot,
            approved_by_admin_id=approved_by_admin_id,
        )
        self._session.add(version)
        await self._session.flush()
        return version

    async def get_by_id(self, version_id: uuid.UUID) -> CompanyProfileVersion | None:
        return await self._session.get(CompanyProfileVersion, version_id)

    async def get_latest_version_number(self, company_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.max(CompanyProfileVersion.version_number)).where(
                CompanyProfileVersion.company_id == company_id
            )
        )
        return result.scalar() or 0
