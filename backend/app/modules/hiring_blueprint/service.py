import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.audit.service import AuditService
from app.modules.auth.models import User
from app.modules.hiring_blueprint.exceptions import (
    HiringBlueprintGenerationError,
    HiringBlueprintNotFoundError,
    MissingRoleBriefError,
)
from app.modules.hiring_blueprint.llm_client import HiringBlueprintLLMClient, LLMRequestError
from app.modules.hiring_blueprint.models import HiringBlueprint
from app.modules.hiring_blueprint.repository import HiringBlueprintRepository
from app.modules.projects.service import ProjectService


class HiringBlueprintService:
    def __init__(
        self, session: AsyncSession, llm_client: HiringBlueprintLLMClient | None = None
    ) -> None:
        # llm_client is only needed by generate_blueprint — get_blueprint (a pure read) doesn't
        # touch the LLM at all, so routes that only read shouldn't need to inject/construct one.
        self._settings = get_settings()
        self._repository = HiringBlueprintRepository(session)
        self._projects = ProjectService(session)
        self._audit = AuditService(session)
        self._llm_client = llm_client

    async def generate_blueprint(self, *, actor: User, project_id: uuid.UUID) -> HiringBlueprint:
        if self._llm_client is None:
            raise ValueError("generate_blueprint requires an llm_client")

        # Raises ProjectNotFoundError (404) if this project doesn't exist or belongs to another
        # tenant — same lookup used by every other project-scoped route.
        project = await self._projects.get_project(
            company_id=actor.company_id, project_id=project_id
        )

        if not project.role_brief:
            raise MissingRoleBriefError()

        try:
            extraction = await self._llm_client.generate_blueprint(
                role_brief=project.role_brief, title=project.title, department=project.department
            )
        except LLMRequestError as exc:
            raise HiringBlueprintGenerationError(str(exc)) from exc

        blueprint = await self._repository.upsert(
            company_id=actor.company_id,
            project_id=project_id,
            role_summary=extraction.role_summary,
            key_responsibilities=extraction.key_responsibilities,
            must_have_qualifications=extraction.must_have_qualifications,
            nice_to_have_qualifications=extraction.nice_to_have_qualifications,
            evaluation_criteria=extraction.evaluation_criteria,
            model_used=self._settings.anthropic_model,
            generated_at=datetime.now(timezone.utc),
        )

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="project.hiring_blueprint_generated",
            target_type="project",
            target_id=project_id,
            extra_data={"model": self._settings.anthropic_model},
        )
        return blueprint

    async def get_blueprint(
        self, *, company_id: uuid.UUID, project_id: uuid.UUID
    ) -> HiringBlueprint:
        blueprint = await self._repository.get_by_project_id(project_id)
        if (
            blueprint is None
            or blueprint.company_id != company_id
            or blueprint.deleted_at is not None
        ):
            raise HiringBlueprintNotFoundError()
        return blueprint
