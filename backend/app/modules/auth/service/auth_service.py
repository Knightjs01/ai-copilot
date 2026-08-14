import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, NamedTuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import webauthn as webauthn_core
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
    InvalidWebAuthnCredentialError,
    SessionNotFoundError,
    WebAuthnCredentialNotFoundError,
)
from app.modules.auth.login_throttle import LoginAttemptTracker
from app.modules.auth.models import (
    RefreshToken,
    TokenPurpose,
    User,
    VerificationToken,
    WebAuthnCredential,
)
from app.modules.auth.permissions import RoleName
from app.modules.auth.repository.roles import RoleRepository
from app.modules.auth.repository.tokens import TokenRepository
from app.modules.auth.repository.users import UserRepository
from app.modules.auth.repository.webauthn import WebAuthnCredentialRepository
from app.modules.auth.service.role_seeding import seed_system_roles
from app.modules.auth.webauthn_challenge_store import WebAuthnChallengeStore
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
        self._webauthn_credentials = WebAuthnCredentialRepository(session)
        self._webauthn_challenges = WebAuthnChallengeStore(realm="company")
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
            # Committed here, not left to get_db's end-of-request commit (app.db.session.get_db)
            # — that dependency rolls back the WHOLE transaction when this method raises right
            # below, which would silently undo the very revocation this branch exists to
            # guarantee. Same reasoning as PhantomPassportService.parse_cv's mid-request commit;
            # expire_on_commit=False (app.db.base) keeps this safe to do mid-request.
            await self._session.commit()
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

    async def begin_webauthn_registration(self, *, user: User) -> str:
        existing = await self._webauthn_credentials.list_for_user(user.id)
        ceremony = webauthn_core.begin_registration(
            user_id=user.id,
            user_name=user.email,
            user_display_name=user.full_name,
            exclude_credential_ids=[
                webauthn_core.decode_credential_id(c.credential_id) for c in existing
            ],
        )
        await self._webauthn_challenges.save(str(user.id), ceremony.challenge)
        return ceremony.options_json

    async def complete_webauthn_registration(
        self, *, user: User, credential_json: dict[str, Any], device_name: str | None
    ) -> WebAuthnCredential:
        challenge = await self._webauthn_challenges.pop(str(user.id))
        if challenge is None:
            raise InvalidOrExpiredTokenError()

        try:
            verified = webauthn_core.verify_registration(
                credential_json=credential_json, expected_challenge=challenge
            )
        except webauthn_core.WebAuthnVerificationError as exc:
            raise InvalidWebAuthnCredentialError() from exc

        credential = await self._webauthn_credentials.create(
            user_id=user.id,
            company_id=user.company_id,
            credential_id=webauthn_core.encode_credential_id(verified.credential_id),
            public_key=webauthn_core.encode_public_key(verified.credential_public_key),
            sign_count=verified.sign_count,
            device_name=device_name,
        )
        await self._audit.record(
            company_id=user.company_id,
            actor_user_id=user.id,
            action="user.webauthn_credential_registered",
            target_type="user",
            target_id=user.id,
            extra_data={"credential_pk_id": str(credential.id), "device_name": device_name},
        )
        return credential

    async def list_webauthn_credentials(self, *, user: User) -> list[WebAuthnCredential]:
        return await self._webauthn_credentials.list_for_user(user.id)

    async def delete_webauthn_credential(self, *, user: User, credential_pk_id: uuid.UUID) -> None:
        credential = await self._webauthn_credentials.get_for_user(
            user_id=user.id, credential_pk_id=credential_pk_id
        )
        if credential is None:
            raise WebAuthnCredentialNotFoundError()
        await self._webauthn_credentials.delete(credential)
        await self._audit.record(
            company_id=user.company_id,
            actor_user_id=user.id,
            action="user.webauthn_credential_deleted",
            target_type="user",
            target_id=user.id,
            extra_data={"credential_pk_id": str(credential_pk_id)},
        )

    async def begin_webauthn_authentication(self, *, email: str) -> str:
        # Anti-enumeration: always build a ceremony and save a challenge, whether or not the
        # email belongs to a real (or passkey-enrolled) account — mirrors login_throttle.py's
        # principle that the response shape must not reveal account existence.
        user = await self._users.get_by_email(email)
        allow_ids: list[bytes] = []
        if user is not None and user.is_active:
            creds = await self._webauthn_credentials.list_for_user(user.id)
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
    ) -> IssuedTokens:
        challenge = await self._webauthn_challenges.pop(
            security.hash_opaque_token(email.strip().lower())
        )
        if challenge is None:
            raise InvalidCredentialsError()

        user = await self._users.get_by_email(email)
        if user is None or not user.is_active:
            raise InvalidCredentialsError()

        credential_id = credential_json.get("id") or credential_json.get("rawId")
        if not isinstance(credential_id, str):
            raise InvalidCredentialsError()
        stored = await self._webauthn_credentials.get_by_credential_id(credential_id)
        if stored is None or stored.user_id != user.id:
            raise InvalidCredentialsError()

        try:
            verified = webauthn_core.verify_authentication(
                credential_json=credential_json,
                expected_challenge=challenge,
                public_key=webauthn_core.decode_public_key(stored.public_key),
                sign_count=stored.sign_count,
            )
        except webauthn_core.WebAuthnVerificationError as exc:
            raise InvalidCredentialsError() from exc

        await self._webauthn_credentials.update_after_use(
            stored, sign_count=verified.new_sign_count
        )
        await self._audit.record(
            company_id=user.company_id,
            actor_user_id=user.id,
            action="user.login_webauthn",
            target_type="user",
            target_id=user.id,
        )
        return await self.issue_tokens(user, user_agent=user_agent, ip_address=ip_address)

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
