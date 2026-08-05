import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.hiring_manager_alignment.models import HiringManagerAlignment


class HiringManagerAlignmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_project_id(self, project_id: uuid.UUID) -> HiringManagerAlignment | None:
        result = await self._session.execute(
            select(HiringManagerAlignment).where(HiringManagerAlignment.project_id == project_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        company_id: uuid.UUID,
        project_id: uuid.UUID,
        top_requirements: list[str],
        submitted_by_id: uuid.UUID,
        submitted_at: datetime,
    ) -> HiringManagerAlignment:
        existing = await self.get_by_project_id(project_id)
        if existing is not None:
            existing.top_requirements = top_requirements
            existing.submitted_by_id = submitted_by_id
            existing.submitted_at = submitted_at
            await self._session.flush()
            return existing

        alignment = HiringManagerAlignment(
            company_id=company_id,
            project_id=project_id,
            top_requirements=top_requirements,
            submitted_by_id=submitted_by_id,
            submitted_at=submitted_at,
        )
        self._session.add(alignment)
        await self._session.flush()
        return alignment

    async def delete_by_project_id(self, project_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(HiringManagerAlignment).where(HiringManagerAlignment.project_id == project_id)
        )
