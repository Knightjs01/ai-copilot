import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.authorization import actor_has_org_wide_access
from app.modules.auth.dependencies import get_current_user_model, get_tenant_db
from app.modules.auth.models import User
from app.modules.candidates.repository import CandidateRepository
from app.modules.candidates.storage import FileStorage, LocalFileStorage
from app.modules.projects.repository import ProjectMemberRepository

_default_storage = LocalFileStorage()


def get_file_storage() -> FileStorage:
    """Overridable via app.dependency_overrides — tests inject a temp-directory-backed storage
    instead of writing into the same directory used for local dev, same pattern as
    app.modules.auth.dependencies.get_email_sender."""

    return _default_storage


async def require_candidate_access(
    candidate_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    session: AsyncSession = Depends(get_tenant_db),
) -> None:
    """Resource-level check on top of require_permission's role check — mirrors
    projects.dependencies.require_project_access, but resolves the candidate's project first
    since candidate_id alone doesn't reveal it. Owner/Admin keep company-wide access; a Member
    must be a ProjectMember of the candidate's project."""

    if await actor_has_org_wide_access(session, actor.id):
        return
    candidate = await CandidateRepository(session).get_by_id(candidate_id)
    if candidate is None or candidate.company_id != actor.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    is_member = await ProjectMemberRepository(session).is_member(
        project_id=candidate.project_id, user_id=actor.id
    )
    if not is_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
