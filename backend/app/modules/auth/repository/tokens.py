import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import MfaBackupCode, RefreshToken, VerificationToken


class TokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_refresh_token(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> RefreshToken:
        now = datetime.now(timezone.utc)
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
            last_used_at=now,
        )
        self._session.add(token)
        await self._session.flush()
        return token

    async def list_active_sessions_for_user(self, user_id: uuid.UUID) -> list[RefreshToken]:
        result = await self._session.execute(
            select(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
            .order_by(RefreshToken.last_used_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_session_for_user(
        self, *, user_id: uuid.UUID, session_id: uuid.UUID
    ) -> RefreshToken | None:
        result = await self._session.execute(
            select(RefreshToken).where(
                RefreshToken.id == session_id,
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self._session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token: RefreshToken) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def revoke_all_refresh_tokens_for_user(
        self, user_id: uuid.UUID, *, except_session_id: uuid.UUID | None = None
    ) -> None:
        conditions = [RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)]
        if except_session_id is not None:
            conditions.append(RefreshToken.id != except_session_id)
        await self._session.execute(
            update(RefreshToken).where(*conditions).values(revoked_at=datetime.now(timezone.utc))
        )
        await self._session.flush()

    async def create_verification_token(
        self, *, user_id: uuid.UUID, purpose: str, token_hash: str, expires_at: datetime
    ) -> VerificationToken:
        token = VerificationToken(
            user_id=user_id, purpose=purpose, token_hash=token_hash, expires_at=expires_at
        )
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_verification_token_by_hash(self, token_hash: str) -> VerificationToken | None:
        result = await self._session.execute(
            select(VerificationToken).where(VerificationToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def mark_verification_token_used(self, token: VerificationToken) -> None:
        token.used_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def invalidate_pending_tokens(self, *, user_id: uuid.UUID, purpose: str) -> None:
        await self._session.execute(
            update(VerificationToken)
            .where(
                VerificationToken.user_id == user_id,
                VerificationToken.purpose == purpose,
                VerificationToken.used_at.is_(None),
            )
            .values(used_at=datetime.now(timezone.utc))
        )
        await self._session.flush()

    async def create_backup_codes(
        self, *, user_id: uuid.UUID, company_id: uuid.UUID, code_hashes: list[str]
    ) -> None:
        for code_hash in code_hashes:
            self._session.add(
                MfaBackupCode(user_id=user_id, company_id=company_id, code_hash=code_hash)
            )
        await self._session.flush()

    async def get_unused_backup_code_by_hash(
        self, *, user_id: uuid.UUID, code_hash: str
    ) -> MfaBackupCode | None:
        result = await self._session.execute(
            select(MfaBackupCode).where(
                MfaBackupCode.user_id == user_id,
                MfaBackupCode.code_hash == code_hash,
                MfaBackupCode.used_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def consume_backup_code(self, code: MfaBackupCode) -> None:
        code.used_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def delete_all_backup_codes_for_user(self, user_id: uuid.UUID) -> None:
        await self._session.execute(delete(MfaBackupCode).where(MfaBackupCode.user_id == user_id))
        await self._session.flush()
