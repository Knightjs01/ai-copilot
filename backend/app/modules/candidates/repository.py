import uuid

from sqlalchemy import select
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
        full_name: str,
        email: str | None,
        phone: str | None,
        source: CandidateSource,
        status: CandidateStatus,
        created_by_id: uuid.UUID,
    ) -> Candidate:
        candidate = Candidate(
            company_id=company_id,
            project_id=project_id,
            full_name=full_name,
            email=email,
            phone=phone,
            source=source.value,
            status=status.value,
            created_by_id=created_by_id,
        )
        self._session.add(candidate)
        await self._session.flush()
        return candidate

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
