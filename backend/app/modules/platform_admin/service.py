from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.auth import security
from app.modules.auth.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidMfaCodeError,
    InvalidOrExpiredTokenError,
    InvalidRoleError,
)
from app.modules.auth.login_throttle import LoginAttemptTracker
from app.modules.platform_admin.audit_service import PlatformAdminAuditService
from app.modules.platform_admin.models import PlatformAdmin
from app.modules.platform_admin.repository import (
    PlatformAdminRepository,
    PlatformAdminTokenRepository,
)
from app.modules.platform_admin.role_repository import PlatformAdminRoleRepository
from app.modules.platform_admin.schemas import PlatformAdminSummary, PurgeAllDataResult

# Tables a "wipe all tenant data" action must never touch: migration bookkeeping, the seeded
# non-tenant permission catalog, and every platform_admin_* table (this admin's own accounts,
# sessions, roles, MFA, audit trail). Deliberately a *prefix* rule, not a hardcoded set of table
# names -- a hardcoded list already went stale twice in this feature's own first day (once for
# the RBAC tables, once for the MFA backup-codes table added right after), each time silently
# wiping every admin's roles or recovery codes on the next purge. Every platform-admin-owned
# table already follows this naming convention (see models.py), so the prefix is the actual
# invariant to encode, not an enumeration that has to be remembered on every future addition.
_PURGE_EXCLUDED_TABLES = frozenset({"alembic_version", "permissions"})
_PURGE_EXCLUDED_PREFIX = "platform_admin"

# Must match the confirmation dialog's required input exactly (frontend/src/components/
# platform-admin/purge-all-data-dialog.tsx) -- checked server-side too, not trusted from the
# client alone, since this is the single most destructive action on the whole site.
PURGE_CONFIRMATION_PHRASE = "DELETE ALL DATA"


_BACKUP_CODE_COUNT = 10


class IssuedAdminTokens(NamedTuple):
    access_token: str
    refresh_token: str


class PlatformAdminAuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._settings = get_settings()
        self._admins = PlatformAdminRepository(session)
        self._tokens = PlatformAdminTokenRepository(session)
        self._audit = PlatformAdminAuditService(session)

    async def login(self, *, email: str, password: str) -> IssuedAdminTokens:
        throttle = LoginAttemptTracker(realm="platform_admin")
        if await throttle.is_locked(email):
            raise InvalidCredentialsError()

        admin = await self._admins.get_by_email(email)
        if admin is None or not admin.is_active:
            await throttle.record_failure(email)
            raise InvalidCredentialsError()
        if not security.verify_password(password, admin.hashed_password):
            await throttle.record_failure(email)
            raise InvalidCredentialsError()

        await throttle.clear(email)
        return await self._issue_tokens(admin)

    async def refresh(self, *, refresh_token_plain: str) -> IssuedAdminTokens:
        token_hash = security.hash_opaque_token(refresh_token_plain)
        stored = await self._tokens.get_refresh_token_by_hash(token_hash)

        if stored is None:
            raise InvalidOrExpiredTokenError()

        if stored.revoked_at is not None:
            # Reuse of an already-rotated token -- treat as theft, kill every session for this
            # admin. Mirrors AuthService.refresh's exact reasoning and mid-method commit (the
            # get_db dependency rolls back the whole transaction when this method raises right
            # below, which would silently undo the revocation this branch exists to guarantee).
            await self._tokens.revoke_all_refresh_tokens_for_admin(stored.admin_id)
            await self._session.commit()
            raise InvalidOrExpiredTokenError()

        if stored.expires_at < datetime.now(timezone.utc):
            raise InvalidOrExpiredTokenError()

        admin = await self._admins.get_by_id(stored.admin_id)
        if admin is None or not admin.is_active:
            raise InvalidOrExpiredTokenError()

        await self._tokens.revoke_refresh_token(stored)
        return await self._issue_tokens(admin)

    async def logout(self, *, refresh_token_plain: str) -> None:
        token_hash = security.hash_opaque_token(refresh_token_plain)
        stored = await self._tokens.get_refresh_token_by_hash(token_hash)
        if stored is not None and stored.revoked_at is None:
            await self._tokens.revoke_refresh_token(stored)

    async def change_password(
        self, *, admin: PlatformAdmin, current_password: str, new_password: str
    ) -> None:
        if not security.verify_password(current_password, admin.hashed_password):
            raise InvalidCredentialsError()
        admin.hashed_password = security.hash_password(new_password)
        # Same reasoning as AuthService.reset_password -- a password change should end every
        # other session, not just leave old refresh tokens quietly valid.
        await self._tokens.revoke_all_refresh_tokens_for_admin(admin.id)

    async def setup_mfa(self, *, admin: PlatformAdmin) -> tuple[str, str]:
        secret = security.generate_totp_secret()
        uri = security.get_totp_provisioning_uri(secret=secret, email=admin.email)
        return secret, uri

    async def enable_mfa(self, *, admin: PlatformAdmin, secret: str, code: str) -> list[str]:
        if not security.verify_totp_code(secret=secret, code=code):
            raise InvalidMfaCodeError()
        admin.mfa_secret_encrypted = security.encrypt_secret(secret)
        admin.mfa_enabled = True

        # Backup codes are the only recovery path if the authenticator is lost -- generated once
        # here and returned in plaintext exactly this one time; only their hashes are ever stored.
        await self._tokens.delete_all_backup_codes_for_admin(admin.id)
        plain_codes = [security.generate_backup_code() for _ in range(_BACKUP_CODE_COUNT)]
        await self._tokens.create_backup_codes(
            admin_id=admin.id,
            code_hashes=[security.hash_opaque_token(c) for c in plain_codes],
        )

        await self._audit.record(
            admin_id=admin.id, action="admin.mfa_enabled", target_type="platform_admin"
        )
        return plain_codes

    async def disable_mfa(self, *, admin: PlatformAdmin, password: str) -> None:
        if not security.verify_password(password, admin.hashed_password):
            raise InvalidCredentialsError()
        admin.mfa_enabled = False
        admin.mfa_secret_encrypted = None
        await self._tokens.delete_all_backup_codes_for_admin(admin.id)
        await self._audit.record(
            admin_id=admin.id, action="admin.mfa_disabled", target_type="platform_admin"
        )

    async def step_up(self, *, admin: PlatformAdmin, password: str, mfa_code: str | None) -> str:
        if not security.verify_password(password, admin.hashed_password):
            raise InvalidCredentialsError()

        if admin.mfa_enabled:
            if not mfa_code or not admin.mfa_secret_encrypted:
                raise InvalidMfaCodeError()
            secret = security.decrypt_secret(admin.mfa_secret_encrypted)
            if not security.verify_totp_code(secret=secret, code=mfa_code):
                backup_code = await self._tokens.get_unused_backup_code_by_hash(
                    admin_id=admin.id,
                    code_hash=security.hash_opaque_token(mfa_code.strip().upper()),
                )
                if backup_code is None:
                    raise InvalidMfaCodeError()
                await self._tokens.consume_backup_code(backup_code)

        await self._audit.record(
            admin_id=admin.id, action="admin.step_up_verified", target_type="platform_admin"
        )
        return security.create_platform_admin_step_up_token(admin_id=admin.id)

    async def _issue_tokens(self, admin: PlatformAdmin) -> IssuedAdminTokens:
        access_token = security.create_platform_admin_access_token(admin_id=admin.id)
        refresh_token_plain = security.generate_opaque_token()
        await self._tokens.create_refresh_token(
            admin_id=admin.id,
            token_hash=security.hash_opaque_token(refresh_token_plain),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=self._settings.refresh_token_expire_days),
        )
        return IssuedAdminTokens(access_token=access_token, refresh_token=refresh_token_plain)


class PurgeConfirmationError(InvalidCredentialsError):
    detail = "Wrong confirmation phrase."


class PlatformAdminDataService:
    """Danger Zone: wipes every real company/candidate table down to nothing, for starting a
    fresh, empty product from a clean slate. Runs on a maintenance-role session (see
    app.db.base.maintenance_session_factory / platform_admin.dependencies.get_maintenance_db) --
    the only role in this database that can touch a FORCE ROW LEVEL SECURITY table outside of a
    single tenant's app.current_company_id context, since this action has no single tenant to
    scope by."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = PlatformAdminAuditService(session)

    async def purge_all_tenant_data(
        self, *, admin: PlatformAdmin, confirmation_phrase: str
    ) -> PurgeAllDataResult:
        # Password + MFA were already re-verified moments ago by require_platform_admin_step_up
        # (the route's own dependency) -- only the typed confirmation phrase is checked here.
        if confirmation_phrase != PURGE_CONFIRMATION_PHRASE:
            raise PurgeConfirmationError()

        tables = await self._tables_in_delete_order()

        for table in tables:
            await self._session.execute(text(f'DELETE FROM "{table}"'))

        await self._audit.record(
            admin_id=admin.id,
            action="tenant_data.purged",
            target_type="platform",
            extra_data={"table_count": len(tables), "tables": tables},
        )
        return PurgeAllDataResult(tables_cleared=len(tables))

    async def _tables_in_delete_order(self) -> list[str]:
        """Every public-schema table except _PURGE_EXCLUDED_TABLES, ordered so a table is only
        deleted once nothing else remaining still holds a foreign key pointing at it (leaves of
        the reference graph first, working up to root tables like companies/candidate_users/
        phantom_passports last). Computed from the live schema, not a hardcoded list, so this
        stays correct as new modules add tables."""

        tables_result = await self._session.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
        all_tables = {
            row[0]
            for row in tables_result
            if row[0] not in _PURGE_EXCLUDED_TABLES
            and not row[0].startswith(_PURGE_EXCLUDED_PREFIX)
        }

        fk_result = await self._session.execute(
            text(
                """
                SELECT tc.table_name AS child_table, ccu.table_name AS parent_table
                FROM information_schema.table_constraints tc
                JOIN information_schema.constraint_column_usage ccu
                    ON tc.constraint_name = ccu.constraint_name
                    AND tc.table_schema = ccu.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
                """
            )
        )
        # referenced_by[parent] = {child, ...} -- child rows must be gone before parent rows.
        referenced_by: dict[str, set[str]] = {table: set() for table in all_tables}
        for child_table, parent_table in fk_result:
            if child_table in all_tables and parent_table in all_tables and child_table != parent_table:
                referenced_by[parent_table].add(child_table)

        ordered: list[str] = []
        remaining = set(all_tables)
        while remaining:
            ready = sorted(t for t in remaining if not (referenced_by[t] & remaining))
            if not ready:
                # A genuine FK cycle -- shouldn't exist in this schema, but delete whatever's
                # left together rather than looping forever.
                ready = sorted(remaining)
            ordered.extend(ready)
            remaining -= set(ready)
        return ordered


class PlatformAdminManagementService:
    """Team page backing service -- lists platform admins and creates new ones with a directly-
    set initial password (no email-invite ceremony yet, see the plan this shipped under)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._admins = PlatformAdminRepository(session)
        self._roles = PlatformAdminRoleRepository(session)

    async def list_admins(self) -> list[PlatformAdminSummary]:
        admins = await self._admins.list_all()
        summaries = []
        for admin in admins:
            roles = await self._roles.get_roles_for_admin(admin.id)
            summaries.append(
                PlatformAdminSummary(
                    id=admin.id,
                    email=admin.email,
                    full_name=admin.full_name,
                    is_active=admin.is_active,
                    roles=[role.name for role in roles],
                    created_at=admin.created_at,
                )
            )
        return summaries

    async def create_admin(
        self, *, full_name: str, email: str, password: str, role_name: str
    ) -> PlatformAdminSummary:
        if await self._admins.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError()

        role = await self._roles.get_role_by_name(role_name)
        if role is None:
            raise InvalidRoleError()

        admin = await self._admins.create(
            full_name=full_name, email=email, hashed_password=security.hash_password(password)
        )
        await self._roles.assign_role_to_admin(admin_id=admin.id, role_id=role.id)

        return PlatformAdminSummary(
            id=admin.id,
            email=admin.email,
            full_name=admin.full_name,
            is_active=admin.is_active,
            roles=[role.name],
            created_at=admin.created_at,
        )
