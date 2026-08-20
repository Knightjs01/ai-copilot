import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.domain_verification import extract_email_domain, is_verified_domain
from app.modules.companies.models import Company
from app.modules.companies.repository import CompanyRepository
from app.modules.companies.schemas import CompanyUpdate

_SLUG_INVALID_CHARS = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    slug = _SLUG_INVALID_CHARS.sub("-", name.lower()).strip("-")
    return slug or "company"


class CompanyService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = CompanyRepository(session)

    async def create_company(self, *, name: str, owner_email: str) -> Company:
        base_slug = slugify(name)
        slug = base_slug
        suffix = 1
        while await self._repository.slug_exists(slug):
            suffix += 1
            slug = f"{base_slug}-{suffix}"

        email_domain = extract_email_domain(owner_email)
        return await self._repository.create(
            name=name,
            slug=slug,
            email_domain=email_domain,
            is_verified_domain=is_verified_domain(email_domain),
        )

    async def get_company(self, company_id: uuid.UUID) -> Company | None:
        return await self._repository.get_by_id(company_id)

    async def update_company(
        self, *, actor_company_id: uuid.UUID, body: CompanyUpdate
    ) -> Company | None:
        company = await self._repository.get_by_id(actor_company_id)
        if company is None:
            return None
        return await self._repository.update(
            company,
            description=body.description,
            culture=body.culture,
            benefits=list(body.benefits),
            size=body.size,
            industry=list(body.industry),
            is_profile_public=body.is_profile_public,
        )

    async def get_public_profile(self, slug: str) -> Company | None:
        company = await self._repository.get_by_slug(slug)
        if company is None or not company.is_profile_public or company.deleted_at is not None:
            return None
        return company
