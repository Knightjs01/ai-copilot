import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.hiring_blueprint.models import HiringBlueprint


class HiringBlueprintRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_project_id(self, project_id: uuid.UUID) -> HiringBlueprint | None:
        result = await self._session.execute(
            select(HiringBlueprint).where(HiringBlueprint.project_id == project_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        company_id: uuid.UUID,
        project_id: uuid.UUID,
        role_summary: str,
        key_responsibilities: list[str],
        must_have_qualifications: list[str],
        nice_to_have_qualifications: list[str],
        evaluation_criteria: list[str],
        model_used: str,
        generated_at: datetime,
    ) -> HiringBlueprint:
        existing = await self.get_by_project_id(project_id)
        if existing is not None:
            existing.role_summary = role_summary
            existing.key_responsibilities = key_responsibilities
            existing.must_have_qualifications = must_have_qualifications
            existing.nice_to_have_qualifications = nice_to_have_qualifications
            existing.evaluation_criteria = evaluation_criteria
            existing.model_used = model_used
            existing.generated_at = generated_at
            await self._session.flush()
            return existing

        blueprint = HiringBlueprint(
            company_id=company_id,
            project_id=project_id,
            role_summary=role_summary,
            key_responsibilities=key_responsibilities,
            must_have_qualifications=must_have_qualifications,
            nice_to_have_qualifications=nice_to_have_qualifications,
            evaluation_criteria=evaluation_criteria,
            model_used=model_used,
            generated_at=generated_at,
        )
        self._session.add(blueprint)
        await self._session.flush()
        return blueprint

    async def delete_by_project_id(self, project_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(HiringBlueprint).where(HiringBlueprint.project_id == project_id)
        )
