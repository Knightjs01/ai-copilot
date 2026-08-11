from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.auth import security
from app.modules.candidate_auth.exceptions import (
    CandidateEmailAlreadyRegisteredError,
    CandidateInvalidCredentialsError,
    CandidateInvalidOrExpiredTokenError,
)
from app.modules.candidate_auth.models import CandidateUser
from app.modules.candidate_auth.repository import (
    CandidateRefreshTokenRepository,
    CandidateUserRepository,
)


class IssuedCandidateTokens(NamedTuple):
    access_token: str
    refresh_token: str


class CandidateAuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._settings = get_settings()
        self._candidates = CandidateUserRepository(session)
        self._tokens = CandidateRefreshTokenRepository(session)

    async def signup(
        self, *, email: str, password: str, full_name: str
    ) -> tuple[CandidateUser, IssuedCandidateTokens]:
        if await self._candidates.get_by_email(email) is not None:
            raise CandidateEmailAlreadyRegisteredError()

        candidate = await self._candidates.create(
            email=email,
            hashed_password=security.hash_password(password),
            full_name=full_name,
        )
        tokens = await self.issue_tokens(candidate)
        return candidate, tokens

    async def login(self, *, email: str, password: str) -> IssuedCandidateTokens:
        candidate = await self._candidates.get_by_email(email)
        if candidate is None or not candidate.is_active:
            raise CandidateInvalidCredentialsError()
        if not security.verify_password(password, candidate.hashed_password):
            raise CandidateInvalidCredentialsError()
        return await self.issue_tokens(candidate)

    async def refresh(self, *, refresh_token_plain: str) -> IssuedCandidateTokens:
        token_hash = security.hash_opaque_token(refresh_token_plain)
        stored = await self._tokens.get_by_hash(token_hash)

        if stored is None:
            raise CandidateInvalidOrExpiredTokenError()
        if stored.revoked_at is not None:
            # Reuse of an already-rotated token — treat as theft, kill every session.
            await self._tokens.revoke_all_for_candidate(stored.candidate_user_id)
            raise CandidateInvalidOrExpiredTokenError()
        if stored.expires_at < datetime.now(timezone.utc):
            raise CandidateInvalidOrExpiredTokenError()

        candidate = await self._candidates.get_by_id(stored.candidate_user_id)
        if candidate is None or not candidate.is_active:
            raise CandidateInvalidOrExpiredTokenError()

        await self._tokens.revoke(stored)
        return await self.issue_tokens(candidate)

    async def logout(self, *, refresh_token_plain: str) -> None:
        token_hash = security.hash_opaque_token(refresh_token_plain)
        stored = await self._tokens.get_by_hash(token_hash)
        if stored is not None and stored.revoked_at is None:
            await self._tokens.revoke(stored)

    async def issue_tokens(self, candidate: CandidateUser) -> IssuedCandidateTokens:
        access_token = security.create_candidate_access_token(candidate_id=candidate.id)
        refresh_token_plain = security.generate_opaque_token()
        await self._tokens.create(
            candidate_user_id=candidate.id,
            token_hash=security.hash_opaque_token(refresh_token_plain),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=self._settings.refresh_token_expire_days),
        )
        return IssuedCandidateTokens(access_token=access_token, refresh_token=refresh_token_plain)
