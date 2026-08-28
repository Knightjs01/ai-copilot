import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, NamedTuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import webauthn as webauthn_core
from app.core.config import get_settings
from app.modules.auth import security
from app.modules.auth.email import (
    ConsoleEmailSender,
    EmailSender,
    EmailSendError,
    build_verification_email,
)
from app.modules.auth.login_throttle import LoginAttemptTracker
from app.modules.auth.webauthn_challenge_store import WebAuthnChallengeStore
from app.modules.candidate_auth.exceptions import (
    CandidateEmailAlreadyRegisteredError,
    CandidateInvalidCredentialsError,
    CandidateInvalidMfaCodeError,
    CandidateInvalidOrExpiredTokenError,
    CandidateInvalidWebAuthnCredentialError,
    CandidateSessionNotFoundError,
    CandidateWebAuthnCredentialNotFoundError,
)
from app.modules.candidate_auth.models import (
    CandidateRefreshToken,
    CandidateUser,
    CandidateWebAuthnCredential,
)
from app.modules.candidate_auth.repository import (
    CandidateMfaBackupCodeRepository,
    CandidateRefreshTokenRepository,
    CandidateUserRepository,
    CandidateVerificationTokenRepository,
    CandidateWebAuthnCredentialRepository,
)

logger = logging.getLogger("app.candidate_auth")

_BACKUP_CODE_COUNT = 10


class IssuedCandidateTokens(NamedTuple):
    access_token: str
    refresh_token: str


class CandidateMfaChallenge(NamedTuple):
    challenge_token: str


class CandidateAuthService:
    def __init__(self, session: AsyncSession, *, email_sender: EmailSender | None = None) -> None:
        self._session = session
        self._settings = get_settings()
        self._candidates = CandidateUserRepository(session)
        self._tokens = CandidateRefreshTokenRepository(session)
        self._verification_tokens = CandidateVerificationTokenRepository(session)
        self._mfa_backup_codes = CandidateMfaBackupCodeRepository(session)
        self._webauthn_credentials = CandidateWebAuthnCredentialRepository(session)
        self._webauthn_challenges = WebAuthnChallengeStore(realm="candidate")
        self._email_sender = email_sender or ConsoleEmailSender()

    async def signup(
        self,
        *,
        email: str,
        password: str,
        first_name: str,
        last_name: str | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[CandidateUser, IssuedCandidateTokens]:
        if await self._candidates.get_by_email(email) is not None:
            raise CandidateEmailAlreadyRegisteredError()

        candidate = await self._candidates.create(
            email=email,
            hashed_password=security.hash_password(password),
            first_name=first_name,
            last_name=last_name,
        )
        try:
            await self._send_verification_email(candidate)
        except EmailSendError:
            # A provider outage/rejection must never block account creation -- the candidate can
            # always retry via POST /candidate-auth/resend-verification (that path still raises,
            # since a user explicitly asking for a resend deserves to know it failed).
            logger.warning(
                "Failed to send verification email during candidate signup for %s",
                candidate.id,
                exc_info=True,
            )
        tokens = await self.issue_tokens(candidate, user_agent=user_agent, ip_address=ip_address)
        return candidate, tokens

    async def login(
        self,
        *,
        email: str,
        password: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
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

        return await self.issue_tokens(candidate, user_agent=user_agent, ip_address=ip_address)

    async def verify_mfa_and_login(
        self,
        *,
        challenge_token: str,
        code: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
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

        return await self.issue_tokens(candidate, user_agent=user_agent, ip_address=ip_address)

    async def refresh(
        self,
        *,
        refresh_token_plain: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> IssuedCandidateTokens:
        token_hash = security.hash_opaque_token(refresh_token_plain)
        stored = await self._tokens.get_by_hash(token_hash)

        if stored is None:
            raise CandidateInvalidOrExpiredTokenError()
        if stored.revoked_at is not None:
            # Reuse of an already-rotated token — treat as theft, kill every session.
            await self._tokens.revoke_all_for_candidate(stored.candidate_user_id)
            # See AuthService.refresh's identical fix for why this commit can't wait for get_db's
            # end-of-request commit — raising immediately below would otherwise roll it back.
            await self._session.commit()
            raise CandidateInvalidOrExpiredTokenError()
        if stored.expires_at < datetime.now(timezone.utc):
            raise CandidateInvalidOrExpiredTokenError()

        candidate = await self._candidates.get_by_id(stored.candidate_user_id)
        if candidate is None or not candidate.is_active:
            raise CandidateInvalidOrExpiredTokenError()

        await self._tokens.revoke(stored)
        return await self.issue_tokens(candidate, user_agent=user_agent, ip_address=ip_address)

    async def logout(self, *, refresh_token_plain: str) -> None:
        token_hash = security.hash_opaque_token(refresh_token_plain)
        stored = await self._tokens.get_by_hash(token_hash)
        if stored is not None and stored.revoked_at is None:
            await self._tokens.revoke(stored)

    async def list_sessions(self, candidate: CandidateUser) -> list[CandidateRefreshToken]:
        return await self._tokens.list_active_sessions_for_candidate(candidate.id)

    async def revoke_session(self, *, candidate: CandidateUser, session_id: uuid.UUID) -> None:
        session = await self._tokens.get_active_session_for_candidate(
            candidate_user_id=candidate.id, session_id=session_id
        )
        if session is None:
            raise CandidateSessionNotFoundError()
        await self._tokens.revoke(session)

    async def revoke_other_sessions(
        self, *, candidate: CandidateUser, current_refresh_token_plain: str | None
    ) -> None:
        current_session_id = None
        if current_refresh_token_plain is not None:
            current = await self._tokens.get_by_hash(
                security.hash_opaque_token(current_refresh_token_plain)
            )
            current_session_id = current.id if current is not None else None
        await self._tokens.revoke_all_for_candidate(
            candidate.id, except_session_id=current_session_id
        )

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

    async def begin_webauthn_registration(self, *, candidate: CandidateUser) -> str:
        existing = await self._webauthn_credentials.list_for_candidate(candidate.id)
        ceremony = webauthn_core.begin_registration(
            user_id=candidate.id,
            user_name=candidate.email,
            user_display_name=candidate.full_name,
            exclude_credential_ids=[
                webauthn_core.decode_credential_id(c.credential_id) for c in existing
            ],
        )
        await self._webauthn_challenges.save(str(candidate.id), ceremony.challenge)
        return ceremony.options_json

    async def complete_webauthn_registration(
        self, *, candidate: CandidateUser, credential_json: dict[str, Any], device_name: str | None
    ) -> CandidateWebAuthnCredential:
        challenge = await self._webauthn_challenges.pop(str(candidate.id))
        if challenge is None:
            raise CandidateInvalidOrExpiredTokenError()

        try:
            verified = webauthn_core.verify_registration(
                credential_json=credential_json, expected_challenge=challenge
            )
        except webauthn_core.WebAuthnVerificationError as exc:
            raise CandidateInvalidWebAuthnCredentialError() from exc

        return await self._webauthn_credentials.create(
            candidate_user_id=candidate.id,
            credential_id=webauthn_core.encode_credential_id(verified.credential_id),
            public_key=webauthn_core.encode_public_key(verified.credential_public_key),
            sign_count=verified.sign_count,
            device_name=device_name,
        )

    async def list_webauthn_credentials(
        self, *, candidate: CandidateUser
    ) -> list[CandidateWebAuthnCredential]:
        return await self._webauthn_credentials.list_for_candidate(candidate.id)

    async def delete_webauthn_credential(
        self, *, candidate: CandidateUser, credential_pk_id: uuid.UUID
    ) -> None:
        credential = await self._webauthn_credentials.get_for_candidate(
            candidate_user_id=candidate.id, credential_pk_id=credential_pk_id
        )
        if credential is None:
            raise CandidateWebAuthnCredentialNotFoundError()
        await self._webauthn_credentials.delete(credential)

    async def begin_webauthn_authentication(self, *, email: str) -> str:
        candidate = await self._candidates.get_by_email(email)
        allow_ids: list[bytes] = []
        if candidate is not None and candidate.is_active:
            creds = await self._webauthn_credentials.list_for_candidate(candidate.id)
            allow_ids = [webauthn_core.decode_credential_id(c.credential_id) for c in creds]

        ceremony = webauthn_core.begin_authentication(allow_credential_ids=allow_ids)
        await self._webauthn_challenges.save(
            security.hash_opaque_token(email.strip().lower()), ceremony.challenge
        )
        return ceremony.options_json

    async def complete_webauthn_authentication(
        self,
        *,
        email: str,
        credential_json: dict[str, Any],
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> IssuedCandidateTokens:
        challenge = await self._webauthn_challenges.pop(
            security.hash_opaque_token(email.strip().lower())
        )
        if challenge is None:
            raise CandidateInvalidCredentialsError()

        candidate = await self._candidates.get_by_email(email)
        if candidate is None or not candidate.is_active:
            raise CandidateInvalidCredentialsError()

        credential_id = credential_json.get("id") or credential_json.get("rawId")
        if not isinstance(credential_id, str):
            raise CandidateInvalidCredentialsError()
        stored = await self._webauthn_credentials.get_by_credential_id(credential_id)
        if stored is None or stored.candidate_user_id != candidate.id:
            raise CandidateInvalidCredentialsError()

        try:
            verified = webauthn_core.verify_authentication(
                credential_json=credential_json,
                expected_challenge=challenge,
                public_key=webauthn_core.decode_public_key(stored.public_key),
                sign_count=stored.sign_count,
            )
        except webauthn_core.WebAuthnVerificationError as exc:
            raise CandidateInvalidCredentialsError() from exc

        await self._webauthn_credentials.update_after_use(
            stored, sign_count=verified.new_sign_count
        )
        return await self.issue_tokens(candidate, user_agent=user_agent, ip_address=ip_address)

    async def issue_tokens(
        self,
        candidate: CandidateUser,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> IssuedCandidateTokens:
        access_token = security.create_candidate_access_token(candidate_id=candidate.id)
        refresh_token_plain = security.generate_opaque_token()
        await self._tokens.create(
            candidate_user_id=candidate.id,
            token_hash=security.hash_opaque_token(refresh_token_plain),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=self._settings.refresh_token_expire_days),
            user_agent=user_agent,
            ip_address=ip_address,
        )
        return IssuedCandidateTokens(access_token=access_token, refresh_token=refresh_token_plain)

    async def request_email_verification(self, *, email: str) -> None:
        candidate = await self._candidates.get_by_email(email)
        if candidate is not None and not candidate.is_email_verified:
            await self._send_verification_email(candidate)

    async def verify_email(self, *, token_plain: str) -> None:
        token_hash = security.hash_opaque_token(token_plain)
        token = await self._verification_tokens.get_by_hash(token_hash)
        if (
            token is None
            or token.used_at is not None
            or token.expires_at < datetime.now(timezone.utc)
        ):
            raise CandidateInvalidOrExpiredTokenError()
        await self._verification_tokens.mark_used(token)

        candidate = await self._candidates.get_by_id(token.candidate_user_id)
        if candidate is None:
            raise CandidateInvalidOrExpiredTokenError()
        candidate.is_email_verified = True

    async def _send_verification_email(self, candidate: CandidateUser) -> None:
        await self._verification_tokens.invalidate_pending_for_candidate(candidate.id)
        token_plain = security.generate_opaque_token()
        await self._verification_tokens.create(
            candidate_user_id=candidate.id,
            token_hash=security.hash_opaque_token(token_plain),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        verify_url = f"{self._settings.frontend_base_url}/shadow/verify-email?token={token_plain}"
        subject, body = build_verification_email(verify_url=verify_url)
        await self._email_sender.send(to=candidate.email, subject=subject, body=body)
