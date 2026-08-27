import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.platform_admin.models import PlatformAdmin, PlatformAdminRefreshToken


class PlatformAdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, admin_id: uuid.UUID) -> PlatformAdmin | None:
        return await self._session.get(PlatformAdmin, admin_id)

    async def get_by_email(self, email: str) -> PlatformAdmin | None:
        result = await self._session.execute(
            select(PlatformAdmin).where(PlatformAdmin.email == email)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[PlatformAdmin]:
        result = await self._session.execute(select(PlatformAdmin).order_by(PlatformAdmin.created_at))
        return list(result.scalars().all())

    async def create(
        self, *, full_name: str, email: str, hashed_password: str
    ) -> PlatformAdmin:
        admin = PlatformAdmin(full_name=full_name, email=email, hashed_password=hashed_password)
        self._session.add(admin)
        await self._session.flush()
        return admin


class PlatformAdminTokenRepository:
    """Mirrors auth.repository.tokens.TokenRepository's refresh-token methods exactly, against
    PlatformAdminRefreshToken instead of RefreshToken."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_refresh_token(
        self, *, admin_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> PlatformAdminRefreshToken:
        token = PlatformAdminRefreshToken(
            admin_id=admin_id, token_hash=token_hash, expires_at=expires_at
        )
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_refresh_token_by_hash(self, token_hash: str) -> PlatformAdminRefreshToken | None:
        result = await self._session.execute(
            select(PlatformAdminRefreshToken).where(
                PlatformAdminRefreshToken.token_hash == token_hash
            )
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token: PlatformAdminRefreshToken) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def revoke_all_refresh_tokens_for_admin(self, admin_id: uuid.UUID) -> None:
        await self._session.execute(
            update(PlatformAdminRefreshToken)
            .where(
                PlatformAdminRefreshToken.admin_id == admin_id,
                PlatformAdminRefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self._session.flush()
