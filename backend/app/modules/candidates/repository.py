import uuid

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.candidates.models import Candidate, CandidateSource, CandidateStatus


class CandidateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        project_id: uuid.UUID,
        callsign: str,
        candidate_ref: str,
        source: CandidateSource,
        status: CandidateStatus,
        created_by_id: uuid.UUID,
    ) -> Candidate:
        candidate = Candidate(
            company_id=company_id,
            project_id=project_id,
            callsign=callsign,
            candidate_ref=candidate_ref,
            source=source.value,
            status=status.value,
            created_by_id=created_by_id,
        )
        self._session.add(candidate)
        await self._session.flush()
        return candidate

    async def callsign_exists_in_project(self, project_id: uuid.UUID, callsign: str) -> bool:
        result = await self._session.execute(
            select(
                exists().where(Candidate.project_id == project_id, Candidate.callsign == callsign)
            )
        )
        return bool(result.scalar_one())

    async def get_by_id(self, candidate_id: uuid.UUID) -> Candidate | None:
        return await self._session.get(Candidate, candidate_id)

    async def list_by_company(
        self,
        company_id: uuid.UUID,
        *,
        project_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Candidate]:
        query = select(Candidate).where(
            Candidate.company_id == company_id, Candidate.deleted_at.is_(None)
        )
        if project_id is not None:
            query = query.where(Candidate.project_id == project_id)
        query = query.order_by(Candidate.created_at.desc()).limit(limit).offset(offset)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def list_all_by_project_id(self, project_id: uuid.UUID) -> list[Candidate]:
        """Unpaginated, includes soft-deleted rows — used only by project_deletion's hard-delete
        orchestration, which needs every candidate under a project regardless of status."""
        result = await self._session.execute(
            select(Candidate).where(Candidate.project_id == project_id)
        )
        return list(result.scalars().all())

    async def delete_by_project_id(self, project_id: uuid.UUID) -> None:
        await self._session.execute(delete(Candidate).where(Candidate.project_id == project_id))
