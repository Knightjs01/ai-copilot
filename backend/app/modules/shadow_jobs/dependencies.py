import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.authorization import actor_has_org_wide_access
from app.modules.auth.dependencies import get_current_user_model, get_tenant_db
from app.modules.auth.models import User
from app.modules.projects.repository import ProjectMemberRepository
from app.modules.shadow_jobs.repository import ShadowJobRepository


async def require_shadow_job_access(
    job_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    session: AsyncSession = Depends(get_tenant_db),
) -> None:
    """Resource-level check on top of require_permission's role check -- mirrors
    projects.dependencies.require_project_access / candidates.dependencies.require_candidate_access.
    Owner/TA Admin keep company-wide access; a Member must either be a ProjectMember of the job's
    linked ATS project, or -- for a Shadow-only job with no linked project (ShadowJob.project_id
    is nullable) -- must have created the job themselves, since there's no project to check
    membership against."""

    if await actor_has_org_wide_access(session, actor.id):
        return
    job = await ShadowJobRepository(session).get_by_id(job_id)
    if job is None or job.company_id != actor.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.project_id is not None:
        is_member = await ProjectMemberRepository(session).is_member(
            project_id=job.project_id, user_id=actor.id
        )
        if not is_member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    elif job.created_by_id != actor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
