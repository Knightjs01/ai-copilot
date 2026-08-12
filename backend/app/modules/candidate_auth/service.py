import uuid
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.auth import security
from app.modules.auth.login_throttle import LoginAttemptTracker
from app.modules.candidate_auth.exceptions import (
    CandidateEmailAlreadyRegisteredError,
    CandidateInvalidCredentialsError,
    CandidateInvalidMfaCodeError,
    CandidateInvalidOrExpiredTokenError,
)
from app.modules.candidate_auth.models import CandidateUser
from app.modules.candidate_auth.repository import (
    CandidateMfaBackupCodeRepository,
    CandidateRefreshTokenRepository,
    CandidateUserRepository,
)

_BACKUP_CODE_COUNT = 10


class IssuedCandidateTokens(NamedTuple):
    access_token: str
    refresh_token: str


class CandidateMfaChallenge(NamedTuple):
    challenge_token: str


class CandidateAuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._settings = get_settings()
        self._candidates = CandidateUserRepository(session)
        self._tokens = CandidateRefreshTokenRepository(session)
        self._mfa_backup_codes = CandidateMfaBackupCodeRepository(session)

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

    async def login(
        self, *, email: str, password: str
    ) -> IssuedCandidateTokens | CandidateMfaChallenge:
        throttle = LoginAttemptTracker(realm="candidate")
        # Same InvalidCredentialsError a wrong password produces — a throttled response must not
        # be distinguishable from an ordinary failed login (see login_throttle.py's docstring).
        if await throttle.is_locked(email):
            raise CandidateInvalidCredentialsError()

        candidate = await self._candidates.get_by_email(email)
        if candidate is None or not candidate.is_active:
            await throttle.record_failure(email)
            raise CandidateInvalidCredentialsError()
        if not security.verify_password(password, candidate.hashed_password):
            await throttle.record_failure(email)
            raise CandidateInvalidCredentialsError()

        await throttle.clear(email)

        if candidate.mfa_enabled:
            return CandidateMfaChallenge(
                challenge_token=security.create_candidate_mfa_challenge_token(
                    candidate_id=candidate.id
                )
            )

        return await self.issue_tokens(candidate)

    async def verify_mfa_and_login(
        self, *, challenge_token: str, code: str
    ) -> IssuedCandidateTokens:
        try:
            payload = security.decode_candidate_mfa_challenge_token(challenge_token)
        except security.TokenError as exc:
            raise CandidateInvalidOrExpiredTokenError() from exc

        candidate = await self._candidates.get_by_id(uuid.UUID(payload["sub"]))
        if candidate is None or not candidate.mfa_enabled or not candidate.mfa_secret_encrypted:
            raise CandidateInvalidOrExpiredTokenError()

        secret = security.decrypt_secret(candidate.mfa_secret_encrypted)
        if not security.verify_totp_code(secret=secret, code=code):
            # Not a valid TOTP code — try it as a backup recovery code before giving up. A
            # backup code is single-use: consuming it here means it can never be used again.
            backup_code = await self._mfa_backup_codes.get_unused_backup_code_by_hash(
                candidate_user_id=candidate.id,
                code_hash=security.hash_opaque_token(code.strip().upper()),
            )
            if backup_code is None:
                raise CandidateInvalidMfaCodeError()
            await self._mfa_backup_codes.consume_backup_code(backup_code)

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

    async def setup_mfa(self, *, candidate: CandidateUser) -> tuple[str, str]:
        secret = security.generate_totp_secret()
        uri = security.get_totp_provisioning_uri(secret=secret, email=candidate.email)
        return secret, uri

    async def enable_mfa(self, *, candidate: CandidateUser, secret: str, code: str) -> list[str]:
        if not security.verify_totp_code(secret=secret, code=code):
            raise CandidateInvalidMfaCodeError()
        candidate.mfa_secret_encrypted = security.encrypt_secret(secret)
        candidate.mfa_enabled = True

        # Backup codes are the only recovery path if the authenticator is lost — generated once
        # here and returned in plaintext exactly this one time; only their hashes are ever stored.
        # Re-enabling (disable then enable again) replaces any codes from a previous enrollment.
        await self._mfa_backup_codes.delete_all_backup_codes_for_candidate(candidate.id)
        plain_codes = [security.generate_backup_code() for _ in range(_BACKUP_CODE_COUNT)]
        await self._mfa_backup_codes.create_backup_codes(
            candidate_user_id=candidate.id,
            code_hashes=[security.hash_opaque_token(c) for c in plain_codes],
        )
        return plain_codes

    async def disable_mfa(self, *, candidate: CandidateUser, password: str) -> None:
        if not security.verify_password(password, candidate.hashed_password):
            raise CandidateInvalidCredentialsError()
        candidate.mfa_enabled = False
        candidate.mfa_secret_encrypted = None
        await self._mfa_backup_codes.delete_all_backup_codes_for_candidate(candidate.id)

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
