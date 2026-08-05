import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.models import Company
from app.modules.companies.repository import CompanyRepository

_SLUG_INVALID_CHARS = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    slug = _SLUG_INVALID_CHARS.sub("-", name.lower()).strip("-")
    return slug or "company"


class CompanyService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = CompanyRepository(session)

    async def create_company(self, name: str) -> Company:
        base_slug = slugify(name)
        slug = base_slug
        suffix = 1
        while await self._repository.slug_exists(slug):
            suffix += 1
            slug = f"{base_slug}-{suffix}"

        return await self._repository.create(name=name, slug=slug)

    async def get_company(self, company_id: uuid.UUID) -> Company | None:
        return await self._repository.get_by_id(company_id)
