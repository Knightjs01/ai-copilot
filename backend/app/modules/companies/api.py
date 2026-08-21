import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user,
    get_current_user_model,
    get_email_sender,
    get_tenant_db,
    require_mfa_enrolled,
    require_permission,
)
from app.modules.auth.email import EmailSender
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.candidates.storage import FileStorage
from app.modules.companies.dependencies import get_media_storage
from app.modules.companies.schemas import (
    AdminCompanySummary,
    CompanyProfileRead,
    CompanyRead,
    CompanyUpdate,
    ProfileReviewRejectBody,
)
from app.modules.companies.service import CompanyService
from app.modules.platform_admin.dependencies import require_platform_admin
from app.modules.platform_admin.models import PlatformAdmin

router = APIRouter(
    prefix="/companies", tags=["companies"], dependencies=[Depends(require_mfa_enrolled)]
)

public_router = APIRouter(prefix="/companies", tags=["companies"])

admin_router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/me", response_model=CompanyRead)
async def get_my_company(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_db),
) -> CompanyRead:
    service = CompanyService(session)
    company = await service.get_company(current_user.company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return service.to_read(company)


@router.patch("/me", response_model=CompanyRead)
async def update_my_company(
    body: CompanyUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    _: CurrentUser = Depends(require_permission(Permissions.COMPANY_MANAGE_SETTINGS)),
    session: AsyncSession = Depends(get_tenant_db),
) -> CompanyRead:
    service = CompanyService(session)
    company = await service.update_company(actor_company_id=current_user.company_id, body=body)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return service.to_read(company)


@router.get("/me/preview", response_model=CompanyProfileRead)
async def preview_my_company_profile(
    current_user: CurrentUser = Depends(get_current_user),
    _: CurrentUser = Depends(require_permission(Permissions.COMPANY_MANAGE_SETTINGS)),
    session: AsyncSession = Depends(get_tenant_db),
) -> CompanyProfileRead:
    return await CompanyService(session).preview_profile(actor_company_id=current_user.company_id)


@router.post("/me/logo", response_model=CompanyRead)
async def upload_logo(
    file: UploadFile = File(...),
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.COMPANY_MANAGE_SETTINGS)),
    session: AsyncSession = Depends(get_tenant_db),
    storage: FileStorage = Depends(get_media_storage),
) -> CompanyRead:
    content = await file.read()
    service = CompanyService(session, storage=storage)
    company = await service.upload_logo(
        actor=actor, content=content, content_type=file.content_type or "application/octet-stream"
    )
    return service.to_read(company)


@router.post("/me/cover-image", response_model=CompanyRead)
async def upload_cover_image(
    file: UploadFile = File(...),
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.COMPANY_MANAGE_SETTINGS)),
    session: AsyncSession = Depends(get_tenant_db),
    storage: FileStorage = Depends(get_media_storage),
) -> CompanyRead:
    content = await file.read()
    service = CompanyService(session, storage=storage)
    company = await service.upload_cover_image(
        actor=actor, content=content, content_type=file.content_type or "application/octet-stream"
    )
    return service.to_read(company)


@router.post("/me/submit-for-review", response_model=CompanyRead)
async def submit_profile_for_review(
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.COMPANY_MANAGE_SETTINGS)),
    session: AsyncSession = Depends(get_tenant_db),
) -> CompanyRead:
    service = CompanyService(session)
    company = await service.submit_for_review(actor=actor)
    return service.to_read(company)


@router.post("/me/pause", response_model=CompanyRead)
async def pause_profile(
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.COMPANY_MANAGE_SETTINGS)),
    session: AsyncSession = Depends(get_tenant_db),
) -> CompanyRead:
    service = CompanyService(session)
    company = await service.pause_profile(actor=actor)
    return service.to_read(company)


@router.post("/me/resume", response_model=CompanyRead)
async def resume_profile(
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.COMPANY_MANAGE_SETTINGS)),
    session: AsyncSession = Depends(get_tenant_db),
) -> CompanyRead:
    service = CompanyService(session)
    company = await service.resume_profile(actor=actor)
    return service.to_read(company)


@public_router.get("/{slug}", response_model=CompanyProfileRead)
async def get_company_profile(
    slug: str, session: AsyncSession = Depends(get_db)
) -> CompanyProfileRead:
    profile = await CompanyService(session).get_public_profile(slug)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return profile


@public_router.get("/{slug}/logo")
async def get_company_logo(
    slug: str,
    session: AsyncSession = Depends(get_db),
    storage: FileStorage = Depends(get_media_storage),
) -> Response:
    content, content_type = await CompanyService(session, storage=storage).read_media(
        slug=slug, field="logo_storage_key"
    )
    return Response(content=content, media_type=content_type)


@public_router.get("/{slug}/cover-image")
async def get_company_cover_image(
    slug: str,
    session: AsyncSession = Depends(get_db),
    storage: FileStorage = Depends(get_media_storage),
) -> Response:
    content, content_type = await CompanyService(session, storage=storage).read_media(
        slug=slug, field="cover_image_storage_key"
    )
    return Response(content=content, media_type=content_type)


@admin_router.get("", response_model=list[AdminCompanySummary])
async def list_companies_for_admin(
    profile_status: str | None = Query(default=None),
    admin: PlatformAdmin = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
) -> list[AdminCompanySummary]:
    pairs = await CompanyService(session).list_companies_with_user_counts(
        profile_status=profile_status
    )
    return [
        AdminCompanySummary(
            id=company.id,
            name=company.name,
            slug=company.slug,
            email_domain=company.email_domain,
            is_verified_domain=company.is_verified_domain,
            status=company.status,
            profile_status=company.profile_status,
            user_count=user_count,
            created_at=company.created_at,
        )
        for company, user_count in pairs
    ]


@admin_router.get("/{company_id}/profile-review/preview", response_model=CompanyProfileRead)
async def preview_company_profile_for_admin(
    company_id: uuid.UUID,
    admin: PlatformAdmin = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
) -> CompanyProfileRead:
    return await CompanyService(session).preview_profile(actor_company_id=company_id)


@admin_router.post("/{company_id}/suspend", response_model=CompanyRead)
async def suspend_company(
    company_id: uuid.UUID,
    admin: PlatformAdmin = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
) -> CompanyRead:
    service = CompanyService(session)
    company = await service.suspend_company(admin_id=admin.id, company_id=company_id)
    return service.to_read(company)


@admin_router.post("/{company_id}/reactivate", response_model=CompanyRead)
async def reactivate_company(
    company_id: uuid.UUID,
    admin: PlatformAdmin = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
) -> CompanyRead:
    service = CompanyService(session)
    company = await service.reactivate_company(admin_id=admin.id, company_id=company_id)
    return service.to_read(company)


@admin_router.post("/{company_id}/profile-review/approve", response_model=CompanyRead)
async def approve_profile_review(
    company_id: uuid.UUID,
    admin: PlatformAdmin = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> CompanyRead:
    service = CompanyService(session, email_sender=email_sender)
    company = await service.approve_profile_review(admin_id=admin.id, company_id=company_id)
    return service.to_read(company)


@admin_router.post("/{company_id}/profile-review/reject", response_model=CompanyRead)
async def reject_profile_review(
    company_id: uuid.UUID,
    body: ProfileReviewRejectBody = ProfileReviewRejectBody(),
    admin: PlatformAdmin = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> CompanyRead:
    service = CompanyService(session, email_sender=email_sender)
    company = await service.reject_profile_review(
        admin_id=admin.id, company_id=company_id, reason=body.reason
    )
    return service.to_read(company)
