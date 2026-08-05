import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import AuditService
from app.modules.auth.models import User
from app.modules.hiring_manager_alignment.exceptions import HiringManagerAlignmentNotFoundError
from app.modules.hiring_manager_alignment.models import HiringManagerAlignment
from app.modules.hiring_manager_alignment.repository import HiringManagerAlignmentRepository
from app.modules.projects.service import ProjectService


class HiringManagerAlignmentService:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = HiringManagerAlignmentRepository(session)
        self._projects = ProjectService(session)
        self._audit = AuditService(session)

    async def submit_alignment(
        self, *, actor: User, project_id: uuid.UUID, top_requirements: list[str]
    ) -> HiringManagerAlignment:
        # Raises ProjectNotFoundError (404) if this project doesn't exist or belongs to another
        # tenant — same lookup used by every other project-scoped route.
        await self._projects.get_project(company_id=actor.company_id, project_id=project_id)

        alignment = await self._repository.upsert(
            company_id=actor.company_id,
            project_id=project_id,
            top_requirements=top_requirements,
            submitted_by_id=actor.id,
            submitted_at=datetime.now(timezone.utc),
        )

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="project.hiring_manager_alignment_submitted",
            target_type="project",
            target_id=project_id,
        )
        return alignment

    async def get_alignment(
        self, *, company_id: uuid.UUID, project_id: uuid.UUID
    ) -> HiringManagerAlignment:
        alignment = await self._repository.get_by_project_id(project_id)
        if (
            alignment is None
            or alignment.company_id != company_id
            or alignment.deleted_at is not None
        ):
            raise HiringManagerAlignmentNotFoundError()
        return alignment
