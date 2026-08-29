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
from app.modules.auth.schemas import UserRead
from app.modules.auth.service.auth_service import AuthService
from app.modules.auth.service.user_service import UserService
from app.modules.candidates.storage import FileStorage
from app.modules.commercial.service import CommercialService
from app.modules.companies.dependencies import get_media_storage
from app.modules.companies.models import Company, CompanyProfileStatus
from app.modules.companies.schemas import (
    AdminCompanySummary,
    AdminCreateCompanyRequest,
    AdminInviteCompanyUserRequest,
    CompanyProfileRead,
    CompanyRead,
    CompanyUpdate,
    ProfileReviewRejectBody,
    ProfileStats,
    PublishChangesRequest,
)
from app.modules.companies.service import CompanyService
from app.modules.platform_admin.dependencies import (
    PlatformAdminContext,
    require_platform_admin_permission,
)
from app.modules.platform_admin.permissions import PlatformAdminPermissions

# Company Onboarding Phase 1's admin-authored routes below are only usable while a company is
# still being onboarded -- once its profile has gone LIVE, editing moves to the (not yet built)
# company self-publish flow, not back through these staff-only routes.
_ONBOARDING_EDITABLE_STATUSES = {
    CompanyProfileStatus.DRAFT.value,
    CompanyProfileStatus.PENDING_REVIEW.value,
}


def _ensure_onboarding_editable(company: Company) -> None:
    if company.profile_status not in _ONBOARDING_EDITABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This company's profile is already live — admin onboarding edits are only "
                "available before activation."
            ),
        )

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


@router.get("/me/profile-stats", response_model=ProfileStats)
async def get_my_profile_stats(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_db),
) -> ProfileStats:
    return await CompanyService(session).get_profile_stats(current_user.company_id)


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
        company_id=actor.company_id,
        content=content,
        content_type=file.content_type or "application/octet-stream",
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
        company_id=actor.company_id,
        content=content,
        content_type=file.content_type or "application/octet-stream",
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


@router.post("/me/publish-changes", response_model=CompanyRead)
async def publish_changes(
    body: PublishChangesRequest,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.COMPANY_MANAGE_SETTINGS)),
    session: AsyncSession = Depends(get_tenant_db),
) -> CompanyRead:
    service = CompanyService(session)
    company = await service.self_publish_changes(actor=actor, confirmed=body.confirmed)
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
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_VIEW)
    ),
    session: AsyncSession = Depends(get_db),
) -> list[AdminCompanySummary]:
    pairs = await CompanyService(session).list_companies_with_user_counts(
        profile_status=profile_status
    )
    plan_code_by_id = {
        plan.id: plan.code for plan in await CommercialService(session).get_plan_catalog()
    }
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
            commercial_plan_code=(
                plan_code_by_id.get(company.commercial_plan_id)
                if company.commercial_plan_id is not None
                else None
            ),
            active_role_limit_override=company.active_role_limit_override,
            is_verified_employer=company.is_verified_employer,
        )
        for company, user_count in pairs
    ]


@admin_router.get("/{company_id}/profile-review/preview", response_model=CompanyProfileRead)
async def preview_company_profile_for_admin(
    company_id: uuid.UUID,
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_VIEW)
    ),
    session: AsyncSession = Depends(get_db),
) -> CompanyProfileRead:
    return await CompanyService(session).preview_profile(actor_company_id=company_id)


@admin_router.post("/{company_id}/suspend", response_model=CompanyRead)
async def suspend_company(
    company_id: uuid.UUID,
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_MANAGE)
    ),
    session: AsyncSession = Depends(get_db),
) -> CompanyRead:
    service = CompanyService(session)
    company = await service.suspend_company(admin_id=admin.id, company_id=company_id)
    return service.to_read(company)


@admin_router.post("/{company_id}/reactivate", response_model=CompanyRead)
async def reactivate_company(
    company_id: uuid.UUID,
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_MANAGE)
    ),
    session: AsyncSession = Depends(get_db),
) -> CompanyRead:
    service = CompanyService(session)
    company = await service.reactivate_company(admin_id=admin.id, company_id=company_id)
    return service.to_read(company)


@admin_router.post("/{company_id}/verify", response_model=CompanyRead)
async def verify_employer(
    company_id: uuid.UUID,
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_MANAGE)
    ),
    session: AsyncSession = Depends(get_db),
) -> CompanyRead:
    service = CompanyService(session)
    company = await service.set_verified_employer(
        admin_id=admin.id, company_id=company_id, is_verified=True
    )
    return service.to_read(company)


@admin_router.post("/{company_id}/unverify", response_model=CompanyRead)
async def unverify_employer(
    company_id: uuid.UUID,
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_MANAGE)
    ),
    session: AsyncSession = Depends(get_db),
) -> CompanyRead:
    service = CompanyService(session)
    company = await service.set_verified_employer(
        admin_id=admin.id, company_id=company_id, is_verified=False
    )
    return service.to_read(company)


@admin_router.post("/{company_id}/profile-review/approve", response_model=CompanyRead)
async def approve_profile_review(
    company_id: uuid.UUID,
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_MANAGE)
    ),
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
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_MANAGE)
    ),
    session: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> CompanyRead:
    service = CompanyService(session, email_sender=email_sender)
    company = await service.reject_profile_review(
        admin_id=admin.id, company_id=company_id, reason=body.reason
    )
    return service.to_read(company)


# --- Company Onboarding Phase 1: platform-admin-only company creation ---------------------------
# Every route below is reachable only via require_platform_admin_permission(COMPANIES_CREATE) --
# there is no equivalent route anywhere on the self-service `router` above, and none is ever
# added there. This is the concrete mechanism keeping the whole onboarding flow confined to the
# platform-admin portal, per the explicit instruction that it must never be reachable company-side.


@admin_router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
async def admin_create_company(
    body: AdminCreateCompanyRequest,
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_CREATE)
    ),
    session: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> CompanyRead:
    company = await AuthService(session, email_sender=email_sender).admin_provision_company(
        admin_id=admin.id,
        company_name=body.company_name,
        owner_email=body.owner_email,
        owner_full_name=body.owner_full_name,
        commercial_plan_code=body.commercial_plan_code,
    )
    return CompanyService(session).to_read(company)


@admin_router.get("/{company_id}/profile", response_model=CompanyRead)
async def get_company_for_admin(
    company_id: uuid.UUID,
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_VIEW)
    ),
    session: AsyncSession = Depends(get_db),
) -> CompanyRead:
    service = CompanyService(session)
    company = await service.get_company(company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return service.to_read(company)


@admin_router.patch("/{company_id}/profile", response_model=CompanyRead)
async def admin_update_company_profile(
    company_id: uuid.UUID,
    body: CompanyUpdate,
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_CREATE)
    ),
    session: AsyncSession = Depends(get_db),
) -> CompanyRead:
    service = CompanyService(session)
    existing = await service.get_company(company_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    _ensure_onboarding_editable(existing)
    company = await service.update_company(actor_company_id=company_id, body=body)
    assert company is not None  # existing was just confirmed non-None above
    return service.to_read(company)


@admin_router.post("/{company_id}/logo", response_model=CompanyRead)
async def admin_upload_logo(
    company_id: uuid.UUID,
    file: UploadFile = File(...),
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_CREATE)
    ),
    session: AsyncSession = Depends(get_db),
    storage: FileStorage = Depends(get_media_storage),
) -> CompanyRead:
    service = CompanyService(session, storage=storage)
    existing = await service.get_company(company_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    _ensure_onboarding_editable(existing)
    content = await file.read()
    company = await service.upload_logo(
        company_id=company_id,
        content=content,
        content_type=file.content_type or "application/octet-stream",
    )
    return service.to_read(company)


@admin_router.post("/{company_id}/cover-image", response_model=CompanyRead)
async def admin_upload_cover_image(
    company_id: uuid.UUID,
    file: UploadFile = File(...),
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_CREATE)
    ),
    session: AsyncSession = Depends(get_db),
    storage: FileStorage = Depends(get_media_storage),
) -> CompanyRead:
    service = CompanyService(session, storage=storage)
    existing = await service.get_company(company_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    _ensure_onboarding_editable(existing)
    content = await file.read()
    company = await service.upload_cover_image(
        company_id=company_id,
        content=content,
        content_type=file.content_type or "application/octet-stream",
    )
    return service.to_read(company)


@admin_router.post("/{company_id}/activate", response_model=CompanyRead)
async def admin_activate_company(
    company_id: uuid.UUID,
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_CREATE)
    ),
    session: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> CompanyRead:
    service = CompanyService(session, email_sender=email_sender)
    company = await service.admin_activate_profile(admin_id=admin.id, company_id=company_id)
    return service.to_read(company)


@admin_router.post(
    "/{company_id}/users/invite", response_model=UserRead, status_code=status.HTTP_201_CREATED
)
async def admin_invite_company_user(
    company_id: uuid.UUID,
    body: AdminInviteCompanyUserRequest,
    admin: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMPANIES_CREATE)
    ),
    session: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> UserRead:
    invited = await UserService(session, email_sender=email_sender).admin_invite_user(
        admin_id=admin.id,
        company_id=company_id,
        email=body.email,
        full_name=body.full_name,
        role_name=body.role_name,
    )
    return UserRead(
        id=invited.id,
        email=invited.email,
        full_name=invited.full_name,
        is_active=invited.is_active,
        is_email_verified=invited.is_email_verified,
        roles=[body.role_name],
    )
