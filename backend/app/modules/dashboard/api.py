import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user_model,
    get_tenant_db,
    require_mfa_enrolled,
    require_permission,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.dashboard.schemas import DashboardStats
from app.modules.dashboard.service import DashboardService

router = APIRouter(
    prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(require_mfa_enrolled)]
)


@router.get("", response_model=DashboardStats)
async def get_dashboard(
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
    project_id: uuid.UUID | None = Query(default=None),
) -> DashboardStats:
    return await DashboardService(session).get_dashboard_stats(
        company_id=actor.company_id, project_id=project_id
    )
