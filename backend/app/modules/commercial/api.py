import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user,
    get_tenant_db,
    require_mfa_enrolled,
)
from app.modules.commercial.schemas import (
    CommercialPlanRead,
    CompanyCommercialSummary,
    PublicCommercialPlanRead,
    UpdateCompanyCommercialRequest,
)
from app.modules.commercial.service import CommercialService
from app.modules.companies.schemas import CompanyRead
from app.modules.companies.service import CompanyService
from app.modules.platform_admin.dependencies import (
    PlatformAdminContext,
    require_platform_admin_permission,
)
from app.modules.platform_admin.permissions import PlatformAdminPermissions

router = APIRouter(
    prefix="/companies", tags=["commercial"], dependencies=[Depends(require_mfa_enrolled)]
)

admin_router = APIRouter(prefix="/platform-admin/commercial", tags=["commercial"])

public_router = APIRouter(prefix="/commercial", tags=["commercial"])


@public_router.get("/plans", response_model=list[PublicCommercialPlanRead])
async def list_public_commercial_plans(
    session: AsyncSession = Depends(get_db),
) -> list[PublicCommercialPlanRead]:
    plans = await CommercialService(session).get_plan_catalog()
    return [PublicCommercialPlanRead.model_validate(p) for p in plans]


@router.get("/me/commercial-summary", response_model=CompanyCommercialSummary)
async def get_my_commercial_summary(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_db),
) -> CompanyCommercialSummary:
    return await CommercialService(session).get_company_summary(current_user.company_id)


@admin_router.get("/plans", response_model=list[CommercialPlanRead])
async def list_commercial_plans(
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMMERCIAL_MANAGE)
    ),
    session: AsyncSession = Depends(get_db),
) -> list[CommercialPlanRead]:
    plans = await CommercialService(session).get_plan_catalog()
    return [CommercialPlanRead.model_validate(p) for p in plans]


@admin_router.post("/companies/{company_id}", response_model=CompanyRead)
async def update_company_commercial(
    company_id: uuid.UUID,
    body: UpdateCompanyCommercialRequest,
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMMERCIAL_MANAGE)
    ),
    session: AsyncSession = Depends(get_db),
) -> CompanyRead:
    fields_set = body.model_fields_set
    company = await CommercialService(session).set_company_commercial(
        admin_id=admin.id,
        company_id=company_id,
        plan_code=body.plan_code,
        plan_code_set="plan_code" in fields_set,
        active_role_limit_override=body.active_role_limit_override,
        active_role_limit_override_set="active_role_limit_override" in fields_set,
        reason=body.reason,
    )
    return CompanyService(session).to_read(company)
