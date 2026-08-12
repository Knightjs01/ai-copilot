import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.schemas import ProjectAnalytics
from app.modules.analytics.service import AnalyticsService
from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user_model,
    get_tenant_db,
    require_mfa_enrolled,
    require_permission,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions

router = APIRouter(
    prefix="/projects", tags=["analytics"], dependencies=[Depends(require_mfa_enrolled)]
)


@router.get("/{project_id}/analytics", response_model=ProjectAnalytics)
async def get_project_analytics(
    project_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ProjectAnalytics:
    return await AnalyticsService(session).get_project_analytics(
        company_id=actor.company_id, project_id=project_id
    )
