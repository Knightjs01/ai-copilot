import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.intelligence.models import IntelligencePack


class IntelligencePackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_candidate_id(self, candidate_id: uuid.UUID) -> IntelligencePack | None:
        result = await self._session.execute(
            select(IntelligencePack).where(IntelligencePack.candidate_id == candidate_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        company_id: uuid.UUID,
        candidate_id: uuid.UUID,
        skills: list[str],
        experience_summary: str,
        education: list[dict[str, Any]],
        narrative_summary: str,
        highlights: list[str],
        industry: str | None,
        years_experience: int | None,
        model_used: str,
        generated_at: datetime,
    ) -> IntelligencePack:
        existing = await self.get_by_candidate_id(candidate_id)
        if existing is not None:
            existing.skills = skills
            existing.experience_summary = experience_summary
            existing.education = education
            existing.narrative_summary = narrative_summary
            existing.highlights = highlights
            existing.industry = industry
            existing.years_experience = years_experience
            existing.model_used = model_used
            existing.generated_at = generated_at
            await self._session.flush()
            return existing

        pack = IntelligencePack(
            company_id=company_id,
            candidate_id=candidate_id,
            skills=skills,
            experience_summary=experience_summary,
            education=education,
            narrative_summary=narrative_summary,
            highlights=highlights,
            industry=industry,
            years_experience=years_experience,
            model_used=model_used,
            generated_at=generated_at,
        )
        self._session.add(pack)
        await self._session.flush()
        return pack

    async def delete_by_candidate_ids(self, candidate_ids: list[uuid.UUID]) -> None:
        if not candidate_ids:
            return
        await self._session.execute(
            delete(IntelligencePack).where(IntelligencePack.candidate_id.in_(candidate_ids))
        )
