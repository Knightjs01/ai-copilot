from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.dependencies import get_tenant_db, require_mfa_enrolled
from app.modules.auth.models import User
from app.modules.candidates.storage import FileStorage, LocalFileStorage
from app.modules.companies.repository import CompanyRepository

# Deliberately NOT wrapped in EncryptingFileStorage (unlike candidates.dependencies.get_file_storage)
# -- a company logo/cover image is public-facing, served back to unauthenticated candidates on the
# profile page, so Fernet-encrypting it at rest would make it unservable.
_default_media_storage = LocalFileStorage()


def get_media_storage() -> FileStorage:
    """Overridable via app.dependency_overrides — tests inject a temp-directory-backed storage,
    same pattern as candidates.dependencies.get_file_storage."""

    return _default_media_storage


async def require_verified_domain(
    user: User = Depends(require_mfa_enrolled),
    session: AsyncSession = Depends(get_tenant_db),
) -> User:
    """Gate for actions with real external/organizational-growth impact — inviting a new user
    into the tenant, publishing a job to the public Shadow board — see
    app/modules/companies/domain_verification.py. Built on require_mfa_enrolled, matching the
    other gate dependencies' composition (auth.dependencies.require_step_up does the same)."""

    company = await CompanyRepository(session).get_by_id(user.company_id)
    if company is None or not company.is_verified_domain:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "This action requires a verified company email domain. "
                "Contact support to get your organization verified."
            ),
        )
    return user
