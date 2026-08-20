import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.models import Company


class CompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, name: str, slug: str, email_domain: str, is_verified_domain: bool
    ) -> Company:
        company = Company(
            name=name,
            slug=slug,
            email_domain=email_domain,
            is_verified_domain=is_verified_domain,
        )
        self._session.add(company)
        await self._session.flush()
        return company

    async def get_by_id(self, company_id: uuid.UUID) -> Company | None:
        return await self._session.get(Company, company_id)

    async def get_by_slug(self, slug: str) -> Company | None:
        result = await self._session.execute(select(Company).where(Company.slug == slug))
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        result = await self._session.execute(select(Company.id).where(Company.slug == slug))
        return result.scalar_one_or_none() is not None

    async def update(
        self,
        company: Company,
        *,
        description: str | None,
        culture: str | None,
        benefits: list[Any],
        size: str | None,
        industry: list[Any],
        is_profile_public: bool,
    ) -> Company:
        company.description = description
        company.culture = culture
        company.benefits = benefits
        company.size = size
        company.industry = industry
        company.is_profile_public = is_profile_public
        await self._session.flush()
        return company
