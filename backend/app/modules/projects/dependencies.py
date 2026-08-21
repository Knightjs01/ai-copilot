import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.authorization import actor_has_org_wide_access
from app.modules.auth.dependencies import get_current_user_model, get_tenant_db
from app.modules.auth.models import User
from app.modules.projects.llm_client import AnthropicProjectsLLMClient, ProjectsLLMClient
from app.modules.projects.repository import ProjectMemberRepository

_default_llm_client: ProjectsLLMClient | None = None


def get_projects_llm_client() -> ProjectsLLMClient:
    """Overridable via app.dependency_overrides — tests inject a FakeProjectsLLMClient instead
    of calling the real Claude API. Constructed lazily (on first real call), not at module
    import time — see app/modules/intelligence/dependencies.py for the full reasoning (an eager
    module-level instance would crash every test's `from app.main import app` when
    ANTHROPIC_API_KEY is unset, which it always is in CI/tests)."""

    global _default_llm_client
    if _default_llm_client is None:
        _default_llm_client = AnthropicProjectsLLMClient()
    return _default_llm_client


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
