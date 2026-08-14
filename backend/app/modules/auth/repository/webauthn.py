import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import WebAuthnCredential


class WebAuthnCredentialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
        credential_id: str,
        public_key: str,
        sign_count: int,
        device_name: str | None,
    ) -> WebAuthnCredential:
        credential = WebAuthnCredential(
            user_id=user_id,
            company_id=company_id,
            credential_id=credential_id,
            public_key=public_key,
            sign_count=sign_count,
            device_name=device_name,
        )
        self._session.add(credential)
        await self._session.flush()
        return credential

    async def get_by_credential_id(self, credential_id: str) -> WebAuthnCredential | None:
        # Deliberately not filtered by company_id — this runs on both the pre-auth app_auth
        # session (login verify, no tenant context yet) and the post-auth app_runtime session.
        # credential_id is globally unique, so the lookup is safe either way; RLS still applies
        # transparently on the app_runtime path.
        result = await self._session.execute(
            select(WebAuthnCredential).where(WebAuthnCredential.credential_id == credential_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID) -> list[WebAuthnCredential]:
        result = await self._session.execute(
            select(WebAuthnCredential)
            .where(WebAuthnCredential.user_id == user_id)
            .order_by(WebAuthnCredential.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_for_user(
        self, *, user_id: uuid.UUID, credential_pk_id: uuid.UUID
    ) -> WebAuthnCredential | None:
        result = await self._session.execute(
            select(WebAuthnCredential).where(
                WebAuthnCredential.id == credential_pk_id,
                WebAuthnCredential.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete(self, credential: WebAuthnCredential) -> None:
        await self._session.delete(credential)
        await self._session.flush()

    async def update_after_use(self, credential: WebAuthnCredential, *, sign_count: int) -> None:
        credential.sign_count = sign_count
        credential.last_used_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def count_for_user(self, user_id: uuid.UUID) -> int:
        credentials = await self.list_for_user(user_id)
        return len(credentials)
