import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.interview_kit.models import InterviewKit


class InterviewKitRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_project_id(self, project_id: uuid.UUID) -> InterviewKit | None:
        result = await self._session.execute(
            select(InterviewKit).where(InterviewKit.project_id == project_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        company_id: uuid.UUID,
        project_id: uuid.UUID,
        questions: list[dict[str, Any]],
        model_used: str,
        generated_at: datetime,
    ) -> InterviewKit:
        existing = await self.get_by_project_id(project_id)
        if existing is not None:
            existing.questions = questions
            existing.model_used = model_used
            existing.generated_at = generated_at
            await self._session.flush()
            return existing

        kit = InterviewKit(
            company_id=company_id,
            project_id=project_id,
            questions=questions,
            model_used=model_used,
            generated_at=generated_at,
        )
        self._session.add(kit)
        await self._session.flush()
        return kit

    async def update_included_flags(
        self, kit: InterviewKit, *, included_flags: list[bool]
    ) -> InterviewKit:
        updated = [
            {**question, "included": flag}
            for question, flag in zip(kit.questions, included_flags, strict=True)
        ]
        kit.questions = updated
        await self._session.flush()
        return kit

    async def delete_by_project_id(self, project_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(InterviewKit).where(InterviewKit.project_id == project_id)
        )
