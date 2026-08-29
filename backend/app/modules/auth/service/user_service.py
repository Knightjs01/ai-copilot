import uuid
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.audit.service import AuditService
from app.modules.auth import security
from app.modules.auth.email import ConsoleEmailSender, EmailSender, build_invite_email
from app.modules.auth.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidRoleError,
    LastOwnerError,
    PermissionDeniedError,
    UserNotFoundError,
)
from app.modules.auth.models import TokenPurpose, User
from app.modules.auth.permissions import RoleName
from app.modules.auth.repository.roles import RoleRepository
from app.modules.auth.repository.tokens import TokenRepository
from app.modules.auth.repository.users import UserRepository
from app.modules.auth.service.auth_service import AuthService, IssuedTokens
from app.modules.companies.service import CompanyService
from app.modules.platform_admin.audit_service import PlatformAdminAuditService


class UserWithRoles(NamedTuple):
    user: User
    role_names: list[str]


class UserService:
    def __init__(self, session: AsyncSession, email_sender: EmailSender | None = None) -> None:
        self._settings = get_settings()
        self._users = UserRepository(session)
        self._roles = RoleRepository(session)
        self._tokens = TokenRepository(session)
        self._companies = CompanyService(session)
        self._audit = AuditService(session)
        self._platform_audit = PlatformAdminAuditService(session)
        self._email_sender = email_sender or ConsoleEmailSender()
        self._auth = AuthService(session, email_sender=self._email_sender)

    async def invite_user(
        self, *, inviter: User, email: str, full_name: str, role_name: str
    ) -> User:
        if role_name == RoleName.OWNER:
            raise PermissionDeniedError("Cannot invite a user directly as Owner")

        if await self._users.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError()

        role = await self._roles.get_role_by_name(inviter.company_id, role_name)
        if role is None:
            raise InvalidRoleError()

        user = await self._users.create(
            company_id=inviter.company_id,
            email=email,
            hashed_password=None,
            full_name=full_name,
            is_active=False,
        )
        await self._roles.assign_role_to_user(user_id=user.id, role_id=role.id)

        token_plain = security.generate_opaque_token()
        await self._tokens.create_verification_token(
            user_id=user.id,
            purpose=TokenPurpose.INVITE,
            token_hash=security.hash_opaque_token(token_plain),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        company = await self._companies.get_company(inviter.company_id)
        accept_url = f"{self._settings.frontend_base_url}/accept-invite?token={token_plain}"
        subject, body = build_invite_email(
            company_name=company.name if company else "your company", accept_url=accept_url
        )
        await self._email_sender.send(to=email, subject=subject, body=body)

        await self._audit.record(
            company_id=inviter.company_id,
            actor_user_id=inviter.id,
            action="user.invited",
            target_type="user",
            target_id=user.id,
            extra_data={"role": role_name},
        )
        return user

    async def admin_invite_user(
        self,
        *,
        admin_id: uuid.UUID,
        company_id: uuid.UUID,
        email: str,
        full_name: str,
        role_name: str,
    ) -> User:
        """Company Onboarding Phase 1's "Company Users" step -- mirrors invite_user's body
        exactly, keyed on an explicit company_id (a platform admin isn't a company User, so
        there's no inviter.company_id to scope from) and audited via PlatformAdminAuditService
        instead of the company-scoped AuditService, since the actor here is platform staff, not
        a member of the company being onboarded. The Owner was already created by
        AuthService.admin_provision_company; this covers every other initial teammate."""

        if role_name == RoleName.OWNER:
            raise PermissionDeniedError("Cannot invite a user directly as Owner")

        if await self._users.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError()

        role = await self._roles.get_role_by_name(company_id, role_name)
        if role is None:
            raise InvalidRoleError()

        user = await self._users.create(
            company_id=company_id,
            email=email,
            hashed_password=None,
            full_name=full_name,
            is_active=False,
        )
        await self._roles.assign_role_to_user(user_id=user.id, role_id=role.id)

        token_plain = security.generate_opaque_token()
        await self._tokens.create_verification_token(
            user_id=user.id,
            purpose=TokenPurpose.INVITE,
            token_hash=security.hash_opaque_token(token_plain),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        company = await self._companies.get_company(company_id)
        accept_url = f"{self._settings.frontend_base_url}/accept-invite?token={token_plain}"
        subject, body = build_invite_email(
            company_name=company.name if company else "your company", accept_url=accept_url
        )
        await self._email_sender.send(to=email, subject=subject, body=body)

        await self._platform_audit.record(
            admin_id=admin_id,
            action="company_user.admin_invited",
            target_type="user",
            target_id=user.id,
            extra_data={"company_id": str(company_id), "role": role_name},
        )
        return user

    async def accept_invite(
        self,
        *,
        token_plain: str,
        password: str,
        full_name: str | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> IssuedTokens:
        token = await self._auth.consume_verification_token(
            token_plain, purpose=TokenPurpose.INVITE
        )
        user = await self._users.get_by_id(token.user_id)
        if user is None:
            raise UserNotFoundError()

        user.hashed_password = security.hash_password(password)
        user.is_active = True
        user.is_email_verified = True
        if full_name:
            user.full_name = full_name

        await self._audit.record(
            company_id=user.company_id,
            actor_user_id=user.id,
            action="user.accepted_invite",
            target_type="user",
            target_id=user.id,
        )
        return await self._auth.issue_tokens(user, user_agent=user_agent, ip_address=ip_address)

    async def list_company_users(
        self, *, company_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[UserWithRoles]:
        users = await self._users.list_by_company(company_id, limit=limit, offset=offset)
        results = []
        for user in users:
            roles = await self._roles.get_roles_for_user(user.id)
            results.append(UserWithRoles(user=user, role_names=[r.name for r in roles]))
        return results

    async def change_user_role(
        self, *, actor: User, target_user_id: uuid.UUID, new_role_name: str
    ) -> None:
        if new_role_name == RoleName.OWNER:
            raise PermissionDeniedError("Promoting to Owner isn't supported by this endpoint")

        target = await self._get_company_member(actor.company_id, target_user_id)
        current_roles = await self._roles.get_roles_for_user(target.id)

        if any(r.name == RoleName.OWNER for r in current_roles):
            await self._ensure_not_last_owner(actor.company_id)

        new_role = await self._roles.get_role_by_name(actor.company_id, new_role_name)
        if new_role is None:
            raise InvalidRoleError()

        for role in current_roles:
            await self._roles.remove_role_from_user(user_id=target.id, role_id=role.id)
        await self._roles.assign_role_to_user(user_id=target.id, role_id=new_role.id)

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="user.role_changed",
            target_type="user",
            target_id=target.id,
            extra_data={"new_role": new_role_name},
        )

    async def remove_user(self, *, actor: User, target_user_id: uuid.UUID) -> None:
        target = await self._get_company_member(actor.company_id, target_user_id)
        current_roles = await self._roles.get_roles_for_user(target.id)

        if any(r.name == RoleName.OWNER for r in current_roles):
            await self._ensure_not_last_owner(actor.company_id)

        target.deleted_at = datetime.now(timezone.utc)
        target.is_active = False
        await self._tokens.revoke_all_refresh_tokens_for_user(target.id)

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="user.removed",
            target_type="user",
            target_id=target.id,
        )

    async def is_company_member(self, *, company_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """For other modules to validate a user reference (e.g. assigning a hiring manager)
        belongs to the expected company, without exposing the raising internal lookup below."""

        user = await self._users.get_by_id(user_id)
        return user is not None and user.company_id == company_id and user.deleted_at is None

    async def _get_company_member(self, company_id: uuid.UUID, user_id: uuid.UUID) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None or user.company_id != company_id or user.deleted_at is not None:
            raise UserNotFoundError()
        return user

    async def _ensure_not_last_owner(self, company_id: uuid.UUID) -> None:
        owner_count = await self._users.count_users_with_role(company_id, RoleName.OWNER)
        if owner_count <= 1:
            raise LastOwnerError()
