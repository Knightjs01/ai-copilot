import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user_model,
    get_tenant_db,
    require_permission,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.candidates.dependencies import get_file_storage
from app.modules.candidates.storage import FileStorage
from app.modules.project_deletion.schemas import BurnProjectResponse
from app.modules.project_deletion.service import ProjectDeletionService

router = APIRouter(prefix="/projects", tags=["project-deletion"])


@router.post("/{project_id}/burn", response_model=BurnProjectResponse)
async def burn_project(
    project_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_DELETE)),
    session: AsyncSession = Depends(get_tenant_db),
    storage: FileStorage = Depends(get_file_storage),
) -> BurnProjectResponse:
    candidate_count = await ProjectDeletionService(session, storage).burn_project(
        actor=actor, project_id=project_id
    )
    return BurnProjectResponse(candidate_count=candidate_count)
