import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.candidate_auth.models import (
    CandidateMfaBackupCode,
    CandidateRefreshToken,
    CandidateUser,
    CandidateWebAuthnCredential,
)


class CandidateUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, email: str, hashed_password: str, full_name: str) -> CandidateUser:
        candidate = CandidateUser(email=email, hashed_password=hashed_password, full_name=full_name)
        self._session.add(candidate)
        await self._session.flush()
        return candidate

    async def get_by_id(self, candidate_id: uuid.UUID) -> CandidateUser | None:
        return await self._session.get(CandidateUser, candidate_id)

    async def get_by_email(self, email: str) -> CandidateUser | None:
        result = await self._session.execute(
            select(CandidateUser).where(CandidateUser.email == email)
        )
        return result.scalar_one_or_none()


class CandidateRefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        candidate_user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> CandidateRefreshToken:
        now = datetime.now(timezone.utc)
        token = CandidateRefreshToken(
            candidate_user_id=candidate_user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
            last_used_at=now,
        )
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_by_hash(self, token_hash: str) -> CandidateRefreshToken | None:
        result = await self._session.execute(
            select(CandidateRefreshToken).where(CandidateRefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke(self, token: CandidateRefreshToken) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def revoke_all_for_candidate(
        self, candidate_user_id: uuid.UUID, *, except_session_id: uuid.UUID | None = None
    ) -> None:
        conditions = [
            CandidateRefreshToken.candidate_user_id == candidate_user_id,
            CandidateRefreshToken.revoked_at.is_(None),
        ]
        if except_session_id is not None:
            conditions.append(CandidateRefreshToken.id != except_session_id)
        await self._session.execute(
            update(CandidateRefreshToken)
            .where(*conditions)
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self._session.flush()

    async def list_active_sessions_for_candidate(
        self, candidate_user_id: uuid.UUID
    ) -> list[CandidateRefreshToken]:
        result = await self._session.execute(
            select(CandidateRefreshToken)
            .where(
                CandidateRefreshToken.candidate_user_id == candidate_user_id,
                CandidateRefreshToken.revoked_at.is_(None),
                CandidateRefreshToken.expires_at > datetime.now(timezone.utc),
            )
            .order_by(CandidateRefreshToken.last_used_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_session_for_candidate(
        self, *, candidate_user_id: uuid.UUID, session_id: uuid.UUID
    ) -> CandidateRefreshToken | None:
        result = await self._session.execute(
            select(CandidateRefreshToken).where(
                CandidateRefreshToken.id == session_id,
                CandidateRefreshToken.candidate_user_id == candidate_user_id,
                CandidateRefreshToken.revoked_at.is_(None),
            )
        )
        return result.scalar_one_or_none()


class CandidateMfaBackupCodeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_backup_codes(
        self, *, candidate_user_id: uuid.UUID, code_hashes: list[str]
    ) -> None:
        for code_hash in code_hashes:
            self._session.add(
                CandidateMfaBackupCode(candidate_user_id=candidate_user_id, code_hash=code_hash)
            )
        await self._session.flush()

    async def get_unused_backup_code_by_hash(
        self, *, candidate_user_id: uuid.UUID, code_hash: str
    ) -> CandidateMfaBackupCode | None:
        result = await self._session.execute(
            select(CandidateMfaBackupCode).where(
                CandidateMfaBackupCode.candidate_user_id == candidate_user_id,
                CandidateMfaBackupCode.code_hash == code_hash,
                CandidateMfaBackupCode.used_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def consume_backup_code(self, code: CandidateMfaBackupCode) -> None:
        code.used_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def delete_all_backup_codes_for_candidate(self, candidate_user_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(CandidateMfaBackupCode).where(
                CandidateMfaBackupCode.candidate_user_id == candidate_user_id
            )
        )
        await self._session.flush()


class CandidateWebAuthnCredentialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        candidate_user_id: uuid.UUID,
        credential_id: str,
        public_key: str,
        sign_count: int,
        device_name: str | None,
    ) -> CandidateWebAuthnCredential:
        credential = CandidateWebAuthnCredential(
            candidate_user_id=candidate_user_id,
            credential_id=credential_id,
            public_key=public_key,
            sign_count=sign_count,
            device_name=device_name,
        )
        self._session.add(credential)
        await self._session.flush()
        return credential

    async def get_by_credential_id(self, credential_id: str) -> CandidateWebAuthnCredential | None:
        result = await self._session.execute(
            select(CandidateWebAuthnCredential).where(
                CandidateWebAuthnCredential.credential_id == credential_id
            )
        )
        return result.scalar_one_or_none()

    async def list_for_candidate(
        self, candidate_user_id: uuid.UUID
    ) -> list[CandidateWebAuthnCredential]:
        result = await self._session.execute(
            select(CandidateWebAuthnCredential)
            .where(CandidateWebAuthnCredential.candidate_user_id == candidate_user_id)
            .order_by(CandidateWebAuthnCredential.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_for_candidate(
        self, *, candidate_user_id: uuid.UUID, credential_pk_id: uuid.UUID
    ) -> CandidateWebAuthnCredential | None:
        result = await self._session.execute(
            select(CandidateWebAuthnCredential).where(
                CandidateWebAuthnCredential.id == credential_pk_id,
                CandidateWebAuthnCredential.candidate_user_id == candidate_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete(self, credential: CandidateWebAuthnCredential) -> None:
        await self._session.delete(credential)
        await self._session.flush()

    async def update_after_use(
        self, credential: CandidateWebAuthnCredential, *, sign_count: int
    ) -> None:
        credential.sign_count = sign_count
        credential.last_used_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def count_for_candidate(self, candidate_user_id: uuid.UUID) -> int:
        return len(await self.list_for_candidate(candidate_user_id))
