import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.prescreen_assessment.models import PrescreenAssessment


class PrescreenAssessmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_candidate_id(self, candidate_id: uuid.UUID) -> PrescreenAssessment | None:
        result = await self._session.execute(
            select(PrescreenAssessment).where(PrescreenAssessment.candidate_id == candidate_id)
        )
        return result.scalar_one_or_none()

    async def upsert_assessment(
        self,
        *,
        company_id: uuid.UUID,
        candidate_id: uuid.UUID,
        fit_rating: str,
        fit_summary: str,
        strengths: list[str],
        gaps: list[str],
        suggested_questions: list[str],
        areas_to_probe: list[str],
        model_used: str,
        generated_at: datetime,
    ) -> PrescreenAssessment:
        existing = await self.get_by_candidate_id(candidate_id)
        if existing is not None:
            existing.fit_rating = fit_rating
            existing.fit_summary = fit_summary
            existing.strengths = strengths
            existing.gaps = gaps
            existing.suggested_questions = suggested_questions
            existing.areas_to_probe = areas_to_probe
            # Regenerating the pre-call assessment invalidates any prior post-call handoff
            # recommendations, since they were derived from the previous gaps/areas_to_probe.
            existing.handoff_recommendations = None
            existing.model_used = model_used
            existing.generated_at = generated_at
            await self._session.flush()
            return existing

        assessment = PrescreenAssessment(
            company_id=company_id,
            candidate_id=candidate_id,
            fit_rating=fit_rating,
            fit_summary=fit_summary,
            strengths=strengths,
            gaps=gaps,
            suggested_questions=suggested_questions,
            areas_to_probe=areas_to_probe,
            model_used=model_used,
            generated_at=generated_at,
        )
        self._session.add(assessment)
        await self._session.flush()
        return assessment

    async def set_handoff_recommendations(
        self, *, assessment: PrescreenAssessment, handoff_recommendations: list[str]
    ) -> PrescreenAssessment:
        assessment.handoff_recommendations = handoff_recommendations
        await self._session.flush()
        return assessment

    async def delete_by_candidate_ids(self, candidate_ids: list[uuid.UUID]) -> None:
        if not candidate_ids:
            return
        await self._session.execute(
            delete(PrescreenAssessment).where(PrescreenAssessment.candidate_id.in_(candidate_ids))
        )

    async def list_by_candidate_ids(
        self, candidate_ids: list[uuid.UUID]
    ) -> list[PrescreenAssessment]:
        if not candidate_ids:
            return []
        result = await self._session.execute(
            select(PrescreenAssessment).where(PrescreenAssessment.candidate_id.in_(candidate_ids))
        )
        return list(result.scalars().all())
