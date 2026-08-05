import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import RefreshToken, VerificationToken


class TokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_refresh_token(
        self, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self._session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token: RefreshToken) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def revoke_all_refresh_tokens_for_user(self, user_id: uuid.UUID) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
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
