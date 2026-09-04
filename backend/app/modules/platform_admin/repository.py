import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.platform_admin.models import (
    PlatformAdmin,
    PlatformAdminMfaBackupCode,
    PlatformAdminRefreshToken,
)


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

    async def mark_notifications_read(self, admin_id: uuid.UUID) -> None:
        await self._session.execute(
            update(PlatformAdmin)
            .where(PlatformAdmin.id == admin_id)
            .values(notifications_read_at=datetime.now(timezone.utc))
        )
        await self._session.flush()


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

    async def create_backup_codes(self, *, admin_id: uuid.UUID, code_hashes: list[str]) -> None:
        for code_hash in code_hashes:
            self._session.add(
                PlatformAdminMfaBackupCode(admin_id=admin_id, code_hash=code_hash)
            )
        await self._session.flush()

    async def get_unused_backup_code_by_hash(
        self, *, admin_id: uuid.UUID, code_hash: str
    ) -> PlatformAdminMfaBackupCode | None:
        result = await self._session.execute(
            select(PlatformAdminMfaBackupCode).where(
                PlatformAdminMfaBackupCode.admin_id == admin_id,
                PlatformAdminMfaBackupCode.code_hash == code_hash,
                PlatformAdminMfaBackupCode.used_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def consume_backup_code(self, code: PlatformAdminMfaBackupCode) -> None:
        code.used_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def delete_all_backup_codes_for_admin(self, admin_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(PlatformAdminMfaBackupCode).where(
                PlatformAdminMfaBackupCode.admin_id == admin_id
            )
        )
