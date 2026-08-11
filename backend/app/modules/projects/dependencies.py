import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.authorization import actor_has_org_wide_access
from app.modules.auth.dependencies import get_current_user_model, get_tenant_db
from app.modules.auth.models import User
from app.modules.projects.repository import ProjectMemberRepository


async def require_project_access(
    project_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    session: AsyncSession = Depends(get_tenant_db),
) -> None:
    """Resource-level check on top of require_permission's role check. Owner/Admin keep
    company-wide access; a Member must additionally be a ProjectMember of this project. Raises
    the same 404 a nonexistent project would — a Member should not be able to tell "doesn't
    exist" apart from "exists but I'm not assigned to it"."""

    if await actor_has_org_wide_access(session, actor.id):
        return
    is_member = await ProjectMemberRepository(session).is_member(
        project_id=project_id, user_id=actor.id
    )
    if not is_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
