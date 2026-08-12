import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity_vault.models import CandidateIdentityVault, IdentityRevealEvent


class IdentityVaultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        candidate_id: uuid.UUID,
        project_id: uuid.UUID,
        full_name_encrypted: str,
        email_encrypted: str | None,
        phone_encrypted: str | None,
    ) -> CandidateIdentityVault:
        vault = CandidateIdentityVault(
            company_id=company_id,
            candidate_id=candidate_id,
            project_id=project_id,
            full_name_encrypted=full_name_encrypted,
            email_encrypted=email_encrypted,
            phone_encrypted=phone_encrypted,
        )
        self._session.add(vault)
        await self._session.flush()
        return vault

    async def get_by_candidate_id(self, candidate_id: uuid.UUID) -> CandidateIdentityVault | None:
        result = await self._session.execute(
            select(CandidateIdentityVault).where(
                CandidateIdentityVault.candidate_id == candidate_id
            )
        )
        return result.scalar_one_or_none()

    async def list_by_project_id(self, project_id: uuid.UUID) -> list[CandidateIdentityVault]:
        result = await self._session.execute(
            select(CandidateIdentityVault).where(CandidateIdentityVault.project_id == project_id)
        )
        return list(result.scalars().all())

    async def delete_by_candidate_ids(self, candidate_ids: list[uuid.UUID]) -> None:
        if not candidate_ids:
            return
        await self._session.execute(
            delete(CandidateIdentityVault).where(
                CandidateIdentityVault.candidate_id.in_(candidate_ids)
            )
        )

    async def count_by_company(self, company_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count()).where(CandidateIdentityVault.company_id == company_id)
        )
        return result.scalar_one()


class IdentityRevealEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        candidate_id: uuid.UUID,
        project_id: uuid.UUID,
        actor_user_id: uuid.UUID | None,
        reason: str,
        ip_address: str | None,
        disclosure_level: str,
    ) -> IdentityRevealEvent:
        event = IdentityRevealEvent(
            company_id=company_id,
            candidate_id=candidate_id,
            project_id=project_id,
            actor_user_id=actor_user_id,
            reason=reason,
            ip_address=ip_address,
            disclosure_level=disclosure_level,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def close(
        self, event: IdentityRevealEvent, *, duration_seconds: int
    ) -> IdentityRevealEvent:
        event.duration_seconds = duration_seconds
        event.closed_at = datetime.now(timezone.utc)
        await self._session.flush()
        return event

    async def get_by_id(self, event_id: uuid.UUID) -> IdentityRevealEvent | None:
        return await self._session.get(IdentityRevealEvent, event_id)

    async def list_by_project_id(
        self, project_id: uuid.UUID, *, limit: int = 20
    ) -> list[IdentityRevealEvent]:
        result = await self._session.execute(
            select(IdentityRevealEvent)
            .where(IdentityRevealEvent.project_id == project_id)
            .order_by(IdentityRevealEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_company(self, company_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count()).where(IdentityRevealEvent.company_id == company_id)
        )
        return result.scalar_one()

    async def delete_by_candidate_ids(self, candidate_ids: list[uuid.UUID]) -> None:
        if not candidate_ids:
            return
        await self._session.execute(
            delete(IdentityRevealEvent).where(IdentityRevealEvent.candidate_id.in_(candidate_ids))
        )
