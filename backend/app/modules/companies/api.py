from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user,
    get_tenant_db,
    require_mfa_enrolled,
    require_permission,
)
from app.modules.auth.permissions import Permissions
from app.modules.companies.schemas import CompanyProfileRead, CompanyRead, CompanyUpdate
from app.modules.companies.service import CompanyService

router = APIRouter(
    prefix="/companies", tags=["companies"], dependencies=[Depends(require_mfa_enrolled)]
)

public_router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/me", response_model=CompanyRead)
async def get_my_company(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_db),
) -> CompanyRead:
    company = await CompanyService(session).get_company(current_user.company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return CompanyRead.model_validate(company)


@router.patch("/me", response_model=CompanyRead)
async def update_my_company(
    body: CompanyUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    _: CurrentUser = Depends(require_permission(Permissions.COMPANY_MANAGE_SETTINGS)),
    session: AsyncSession = Depends(get_tenant_db),
) -> CompanyRead:
    company = await CompanyService(session).update_company(
        actor_company_id=current_user.company_id, body=body
    )
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return CompanyRead.model_validate(company)


@public_router.get("/{slug}", response_model=CompanyProfileRead)
async def get_company_profile(
    slug: str, session: AsyncSession = Depends(get_db)
) -> CompanyProfileRead:
    company = await CompanyService(session).get_public_profile(slug)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return CompanyProfileRead.model_validate(company)
