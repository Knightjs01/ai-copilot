import uuid
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.audit.service import AuditService
from app.modules.auth import security
from app.modules.auth.email import (
    ConsoleEmailSender,
    EmailSender,
    build_password_reset_email,
    build_verification_email,
)
from app.modules.auth.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidMfaCodeError,
    InvalidOrExpiredTokenError,
    SessionNotFoundError,
)
from app.modules.auth.login_throttle import LoginAttemptTracker
from app.modules.auth.models import RefreshToken, TokenPurpose, User, VerificationToken
from app.modules.auth.permissions import RoleName
from app.modules.auth.repository.roles import RoleRepository
from app.modules.auth.repository.tokens import TokenRepository
from app.modules.auth.repository.users import UserRepository
from app.modules.auth.service.role_seeding import seed_system_roles
from app.modules.companies.service import CompanyService


_BACKUP_CODE_COUNT = 10


class IssuedTokens(NamedTuple):
    access_token: str
    refresh_token: str


class MfaChallenge(NamedTuple):
    challenge_token: str


class AuthService:
    def __init__(self, session: AsyncSession, email_sender: EmailSender | None = None) -> None:
        self._session = session
        self._settings = get_settings()
        self._users = UserRepository(session)
        self._roles = RoleRepository(session)
        self._tokens = TokenRepository(session)
        self._companies = CompanyService(session)
        self._audit = AuditService(session)
        self._email_sender = email_sender or ConsoleEmailSender()

    async def signup(
        self,
        *,
        company_name: str,
        email: str,
        password: str,
        full_name: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[User, IssuedTokens]:
        if await self._users.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError()

        company = await self._companies.create_company(name=company_name, owner_email=email)
        roles = await seed_system_roles(self._roles, company.id)

        user = await self._users.create(
            company_id=company.id,
            email=email,
            hashed_password=security.hash_password(password),
            full_name=full_name,
        )
        await self._roles.assign_role_to_user(user_id=user.id, role_id=roles[RoleName.OWNER].id)

        await self._send_verification_email(user)
        await self._audit.record(
            company_id=company.id,
            actor_user_id=user.id,
            action="user.signup",
            target_type="user",
            target_id=user.id,
        )

        tokens = await self.issue_tokens(user, user_agent=user_agent, ip_address=ip_address)
        return user, tokens

    async def login(
        self,
        *,
        email: str,
        password: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> IssuedTokens | MfaChallenge:
        throttle = LoginAttemptTracker(realm="company")
        # Same InvalidCredentialsError a wrong password produces — a throttled response must not
        # be distinguishable from an ordinary failed login (see login_throttle.py's docstring).
        if await throttle.is_locked(email):
            raise InvalidCredentialsError()

        user = await self._users.get_by_email(email)
        # Split from the verify_password check below: an invited-but-not-yet-accepted user has
        # no password at all, which is a distinct case from a wrong password, and narrows
        # hashed_password to str for the type checker on the line after.
        if user is None or not user.is_active or user.hashed_password is None:
            await throttle.record_failure(email)
            raise InvalidCredentialsError()
        if not security.verify_password(password, user.hashed_password):
            await throttle.record_failure(email)
            raise InvalidCredentialsError()

        await throttle.clear(email)

        if user.mfa_enabled:
            return MfaChallenge(
                challenge_token=security.create_mfa_challenge_token(user_id=user.id)
            )

        await self._audit.record(
            company_id=user.company_id,
            actor_user_id=user.id,
            action="user.login",
            target_type="user",
            target_id=user.id,
        )
        return await self.issue_tokens(user, user_agent=user_agent, ip_address=ip_address)

    async def verify_mfa_and_login(
        self,
        *,
        challenge_token: str,
        code: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> IssuedTokens:
        try:
            payload = security.decode_mfa_challenge_token(challenge_token)
        except security.TokenError as exc:
            raise InvalidOrExpiredTokenError() from exc

        user = await self._users.get_by_id(uuid.UUID(payload["sub"]))
        if user is None or not user.mfa_enabled or not user.mfa_secret_encrypted:
            raise InvalidOrExpiredTokenError()

        secret = security.decrypt_secret(user.mfa_secret_encrypted)
        used_backup_code = False
        if not security.verify_totp_code(secret=secret, code=code):
            # Not a valid TOTP code — try it as a backup recovery code before giving up. A
            # backup code is single-use: consuming it here means it can never be used again,
            # even if the same value is submitted twice.
            backup_code = await self._tokens.get_unused_backup_code_by_hash(
                user_id=user.id, code_hash=security.hash_opaque_token(code.strip().upper())
            )
            if backup_code is None:
                raise InvalidMfaCodeError()
            await self._tokens.consume_backup_code(backup_code)
            used_backup_code = True

        await self._audit.record(
            company_id=user.company_id,
            actor_user_id=user.id,
            action="user.login_mfa_backup_code" if used_backup_code else "user.login_mfa",
            target_type="user",
            target_id=user.id,
        )
        return await self.issue_tokens(user, user_agent=user_agent, ip_address=ip_address)

    async def refresh(
        self,
        *,
        refresh_token_plain: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> IssuedTokens:
        token_hash = security.hash_opaque_token(refresh_token_plain)
        stored = await self._tokens.get_refresh_token_by_hash(token_hash)

        if stored is None:
            raise InvalidOrExpiredTokenError()

        if stored.revoked_at is not None:
            # Reuse of an already-rotated token — treat as theft, kill every session for this user.
            await self._tokens.revoke_all_refresh_tokens_for_user(stored.user_id)
            raise InvalidOrExpiredTokenError()

        if stored.expires_at < datetime.now(timezone.utc):
            raise InvalidOrExpiredTokenError()

        user = await self._users.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise InvalidOrExpiredTokenError()

        await self._tokens.revoke_refresh_token(stored)
        return await self.issue_tokens(user, user_agent=user_agent, ip_address=ip_address)

    async def logout(self, *, refresh_token_plain: str) -> None:
        token_hash = security.hash_opaque_token(refresh_token_plain)
        stored = await self._tokens.get_refresh_token_by_hash(token_hash)
        if stored is not None and stored.revoked_at is None:
            await self._tokens.revoke_refresh_token(stored)

    async def list_sessions(self, user: User) -> list[RefreshToken]:
        return await self._tokens.list_active_sessions_for_user(user.id)

    async def revoke_session(self, *, user: User, session_id: uuid.UUID) -> None:
        session = await self._tokens.get_active_session_for_user(
            user_id=user.id, session_id=session_id
        )
        if session is None:
            raise SessionNotFoundError()
        await self._tokens.revoke_refresh_token(session)
        await self._audit.record(
            company_id=user.company_id,
            actor_user_id=user.id,
            action="user.session_revoked",
            target_type="refresh_token",
            target_id=session_id,
        )

    async def revoke_other_sessions(
        self, *, user: User, current_refresh_token_plain: str | None
    ) -> None:
        current_session_id = None
        if current_refresh_token_plain is not None:
            current = await self._tokens.get_refresh_token_by_hash(
                security.hash_opaque_token(current_refresh_token_plain)
            )
            current_session_id = current.id if current is not None else None
        await self._tokens.revoke_all_refresh_tokens_for_user(
            user.id, except_session_id=current_session_id
        )
        await self._audit.record(
            company_id=user.company_id,
            actor_user_id=user.id,
            action="user.other_sessions_revoked",
            target_type="user",
            target_id=user.id,
        )

    async def request_email_verification(self, *, email: str) -> None:
        user = await self._users.get_by_email(email)
        if user is not None and not user.is_email_verified:
            await self._send_verification_email(user)

    async def verify_email(self, *, token_plain: str) -> None:
        token = await self.consume_verification_token(
            token_plain, purpose=TokenPurpose.EMAIL_VERIFY
        )
        user = await self._users.get_by_id(token.user_id)
        if user is None:
            raise InvalidOrExpiredTokenError()
        user.is_email_verified = True

    async def request_password_reset(self, *, email: str) -> None:
        user = await self._users.get_by_email(email)
        if user is None:
            return  # Don't reveal whether the email exists.

        await self._tokens.invalidate_pending_tokens(
            user_id=user.id, purpose=TokenPurpose.PASSWORD_RESET
        )
        token_plain = security.generate_opaque_token()
        await self._tokens.create_verification_token(
            user_id=user.id,
            purpose=TokenPurpose.PASSWORD_RESET,
            token_hash=security.hash_opaque_token(token_plain),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        reset_url = f"{self._settings.frontend_base_url}/reset-password?token={token_plain}"
        subject, body = build_password_reset_email(reset_url=reset_url)
        await self._email_sender.send(to=user.email, subject=subject, body=body)

    async def reset_password(self, *, token_plain: str, new_password: str) -> None:
        token = await self.consume_verification_token(
            token_plain, purpose=TokenPurpose.PASSWORD_RESET
        )
        user = await self._users.get_by_id(token.user_id)
        if user is None:
            raise InvalidOrExpiredTokenError()

        user.hashed_password = security.hash_password(new_password)
        await self._tokens.revoke_all_refresh_tokens_for_user(user.id)
        await self._audit.record(
            company_id=user.company_id,
            actor_user_id=user.id,
            action="user.password_reset",
            target_type="user",
            target_id=user.id,
        )

    async def setup_mfa(self, *, user: User) -> tuple[str, str]:
        secret = security.generate_totp_secret()
        uri = security.get_totp_provisioning_uri(secret=secret, email=user.email)
        return secret, uri

    async def enable_mfa(self, *, user: User, secret: str, code: str) -> list[str]:
        if not security.verify_totp_code(secret=secret, code=code):
            raise InvalidMfaCodeError()
        user.mfa_secret_encrypted = security.encrypt_secret(secret)
        user.mfa_enabled = True

        # Backup codes are the only recovery path if the authenticator is lost — generated once
        # here and returned in plaintext exactly this one time; only their hashes are ever stored.
        # Re-enabling (disable then enable again) replaces any codes from a previous enrollment.
        await self._tokens.delete_all_backup_codes_for_user(user.id)
        plain_codes = [security.generate_backup_code() for _ in range(_BACKUP_CODE_COUNT)]
        await self._tokens.create_backup_codes(
            user_id=user.id,
            company_id=user.company_id,
            code_hashes=[security.hash_opaque_token(c) for c in plain_codes],
        )

        await self._audit.record(
            company_id=user.company_id,
            actor_user_id=user.id,
            action="user.mfa_enabled",
            target_type="user",
            target_id=user.id,
        )
        return plain_codes

    async def disable_mfa(self, *, user: User, password: str) -> None:
        # An authenticated user (get_current_user_model already required is_active=True) always
        # has a real password — only invited-but-not-accepted users lack one, and they can't
        # authenticate at all — but narrow explicitly for the type checker rather than assume it.
        if user.hashed_password is None or not security.verify_password(
            password, user.hashed_password
        ):
            raise InvalidCredentialsError()
        user.mfa_enabled = False
        user.mfa_secret_encrypted = None
        await self._tokens.delete_all_backup_codes_for_user(user.id)
        await self._audit.record(
            company_id=user.company_id,
            actor_user_id=user.id,
            action="user.mfa_disabled",
            target_type="user",
            target_id=user.id,
        )

    async def step_up(self, *, user: User, password: str, mfa_code: str | None) -> str:
        # Same narrowing as disable_mfa: an authenticated user always has a real password.
        if user.hashed_password is None or not security.verify_password(
            password, user.hashed_password
        ):
            raise InvalidCredentialsError()

        if user.mfa_enabled:
            if not mfa_code or not user.mfa_secret_encrypted:
                raise InvalidMfaCodeError()
            secret = security.decrypt_secret(user.mfa_secret_encrypted)
            if not security.verify_totp_code(secret=secret, code=mfa_code):
                backup_code = await self._tokens.get_unused_backup_code_by_hash(
                    user_id=user.id, code_hash=security.hash_opaque_token(mfa_code.strip().upper())
                )
                if backup_code is None:
                    raise InvalidMfaCodeError()
                await self._tokens.consume_backup_code(backup_code)

        await self._audit.record(
            company_id=user.company_id,
            actor_user_id=user.id,
            action="user.step_up_verified",
            target_type="user",
            target_id=user.id,
        )
        return security.create_step_up_token(user_id=user.id)

    async def _send_verification_email(self, user: User) -> None:
        await self._tokens.invalidate_pending_tokens(
            user_id=user.id, purpose=TokenPurpose.EMAIL_VERIFY
        )
        token_plain = security.generate_opaque_token()
        await self._tokens.create_verification_token(
            user_id=user.id,
            purpose=TokenPurpose.EMAIL_VERIFY,
            token_hash=security.hash_opaque_token(token_plain),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        verify_url = f"{self._settings.frontend_base_url}/verify-email?token={token_plain}"
        subject, body = build_verification_email(verify_url=verify_url)
        await self._email_sender.send(to=user.email, subject=subject, body=body)

    async def consume_verification_token(
        self, token_plain: str, *, purpose: str
    ) -> VerificationToken:
        token_hash = security.hash_opaque_token(token_plain)
        token = await self._tokens.get_verification_token_by_hash(token_hash)
        if (
            token is None
            or token.purpose != purpose
            or token.used_at is not None
            or token.expires_at < datetime.now(timezone.utc)
        ):
            raise InvalidOrExpiredTokenError()
        await self._tokens.mark_verification_token_used(token)
        return token

    async def issue_tokens(
        self,
        user: User,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> IssuedTokens:
        access_token = security.create_access_token(user_id=user.id, company_id=user.company_id)
        refresh_token_plain = security.generate_opaque_token()
        await self._tokens.create_refresh_token(
            user_id=user.id,
            token_hash=security.hash_opaque_token(refresh_token_plain),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=self._settings.refresh_token_expire_days),
            user_agent=user_agent,
            ip_address=ip_address,
        )
        return IssuedTokens(access_token=access_token, refresh_token=refresh_token_plain)
