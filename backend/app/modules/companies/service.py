import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.audit.service import AuditService
from app.modules.auth.email import (
    EmailSender,
    build_profile_approved_email,
    build_profile_rejected_email,
)
from app.modules.auth.models import User
from app.modules.auth.repository.users import UserRepository
from app.modules.candidates.models import CandidateStatus
from app.modules.candidates.repository import CandidateRepository
from app.modules.candidates.storage import FileStorage
from app.modules.commercial.repository import CommercialPlanRepository
from app.modules.companies.domain_verification import extract_email_domain, is_verified_domain
from app.modules.companies.exceptions import (
    CompanyAlreadyInStatusError,
    CompanyNotFoundError,
    InvalidMediaFileError,
    InvalidProfileTransitionError,
)
from app.modules.companies.models import Company, CompanyProfileStatus, CompanyStatus
from app.modules.companies.repository import CompanyProfileVersionRepository, CompanyRepository
from app.modules.companies.schemas import (
    CompanyProfileRead,
    CompanyRead,
    CompanyUpdate,
    ProfileStats,
)
from app.modules.platform_admin.audit_service import PlatformAdminAuditService
from app.modules.projects.repository import ProjectRepository

_SLUG_INVALID_CHARS = re.compile(r"[^a-z0-9]+")

# Every new company starts on Core -- see commercial/. Assigned at creation, not left null,
# so a freshly-provisioned company is never accidentally unlimited (get_effective_limit treats a
# null plan the same as "no limit configured" -- that's meant for a Scale company an admin
# hasn't set a number for yet, not the default state of a brand-new signup).
_DEFAULT_COMMERCIAL_PLAN_CODE = "core"

# Mirrors dashboard/service.py's own _IN_PROCESS_STATUSES exactly -- kept as a separate literal
# copy rather than importing it, same reasoning already applied to the permissions catalog
# migration keeping its own copy: a small, stable constant, not worth a cross-module dependency.
_IN_PROCESS_CANDIDATE_STATUSES = {
    CandidateStatus.NEW.value,
    CandidateStatus.SCREENING.value,
    CandidateStatus.INTERVIEWING.value,
    CandidateStatus.OFFER.value,
}

_ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}

# States a company can freely submit a review from -- re-submitting from LIVE queues a new
# review without hiding the currently-live version (the old snapshot stays public until the new
# one is approved). Not valid from PENDING_REVIEW (already queued) or SUSPENDED (staff must lift
# the suspension first).
_SUBMITTABLE_STATUSES = {
    CompanyProfileStatus.DRAFT.value,
    CompanyProfileStatus.LIVE.value,
    CompanyProfileStatus.PAUSED.value,
}


def slugify(name: str) -> str:
    slug = _SLUG_INVALID_CHARS.sub("-", name.lower()).strip("-")
    return slug or "company"


def is_profile_publicly_visible(company: Company) -> bool:
    """Visible whenever an approved snapshot exists, regardless of profile_status, except when
    explicitly hidden (PAUSED/SUSPENDED) -- a new pending review must not un-publish the still-
    live, last-approved version while it waits on a decision. Shared by get_public_profile and
    by anything (Shadow job listings, saved jobs) deciding whether to link out to the profile
    page -- a link should exist exactly when the page it points to would actually resolve."""

    return company.current_profile_version_id is not None and company.profile_status not in (
        CompanyProfileStatus.PAUSED.value,
        CompanyProfileStatus.SUSPENDED.value,
    )


class CompanyService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        storage: FileStorage | None = None,
        email_sender: EmailSender | None = None,
    ) -> None:
        self._settings = get_settings()
        self._session = session
        self._repository = CompanyRepository(session)
        self._versions = CompanyProfileVersionRepository(session)
        self._commercial_plans = CommercialPlanRepository(session)
        self._candidates = CandidateRepository(session)
        self._projects = ProjectRepository(session)
        self._users = UserRepository(session)
        self._audit = AuditService(session)
        self._platform_audit = PlatformAdminAuditService(session)
        self._storage = storage
        self._email_sender = email_sender

    async def create_company(self, *, name: str, owner_email: str) -> Company:
        base_slug = slugify(name)
        slug = base_slug
        suffix = 1
        while await self._repository.slug_exists(slug):
            suffix += 1
            slug = f"{base_slug}-{suffix}"

        email_domain = extract_email_domain(owner_email)
        default_plan = await self._commercial_plans.get_by_code(_DEFAULT_COMMERCIAL_PLAN_CODE)
        return await self._repository.create(
            name=name,
            slug=slug,
            email_domain=email_domain,
            is_verified_domain=is_verified_domain(email_domain),
            commercial_plan_id=default_plan.id if default_plan is not None else None,
        )

    async def get_company(self, company_id: uuid.UUID) -> Company | None:
        return await self._repository.get_by_id(company_id)

    # --- Self-service: draft editing ------------------------------------------------------------

    async def update_company(
        self, *, actor_company_id: uuid.UUID, body: CompanyUpdate
    ) -> Company | None:
        company = await self._repository.get_by_id(actor_company_id)
        if company is None:
            return None
        fields_set = body.model_fields_set
        return await self._repository.update(
            company,
            description=body.description if "description" in fields_set else company.description,
            culture=body.culture if "culture" in fields_set else company.culture,
            benefits=(
                list(body.benefits)
                if "benefits" in fields_set and body.benefits is not None
                else company.benefits
            ),
            size=body.size if "size" in fields_set else company.size,
            industry=(
                list(body.industry)
                if "industry" in fields_set and body.industry is not None
                else company.industry
            ),
            hiring_process_overview=(
                body.hiring_process_overview
                if "hiring_process_overview" in fields_set
                else company.hiring_process_overview
            ),
            tagline=body.tagline if "tagline" in fields_set else company.tagline,
            website=body.website if "website" in fields_set else company.website,
            founded_year=(
                body.founded_year if "founded_year" in fields_set else company.founded_year
            ),
            headquarters=(
                body.headquarters if "headquarters" in fields_set else company.headquarters
            ),
            employee_count=(
                body.employee_count if "employee_count" in fields_set else company.employee_count
            ),
            values=(
                [item.model_dump() for item in body.values]
                if "values" in fields_set and body.values is not None
                else company.values
            ),
            looking_for=(
                list(body.looking_for)
                if "looking_for" in fields_set and body.looking_for is not None
                else company.looking_for
            ),
            hiring_highlights=(
                [item.model_dump() for item in body.hiring_highlights]
                if "hiring_highlights" in fields_set and body.hiring_highlights is not None
                else company.hiring_highlights
            ),
        )

    async def set_verified_employer(
        self, *, admin_id: uuid.UUID, company_id: uuid.UUID, is_verified: bool
    ) -> Company:
        """The one honest verification signal -- see Company.is_verified_employer's docstring.
        Deliberately no "already in that state" guard (unlike suspend/reactivate): this is a
        content flag an admin can freely re-confirm, not a lifecycle transition where re-entering
        the same state would be a meaningful error."""

        company = await self._repository.get_by_id(company_id)
        if company is None:
            raise CompanyNotFoundError()
        company.is_verified_employer = is_verified
        await self._session.flush()
        await self._platform_audit.record(
            admin_id=admin_id,
            action="company.verified_employer_set",
            target_type="company",
            target_id=company.id,
            extra_data={"company_name": company.name, "is_verified": is_verified},
        )
        return company

    async def get_profile_stats(self, company_id: uuid.UUID) -> ProfileStats:
        company = await self._repository.get_by_id(company_id)
        if company is None:
            raise CompanyNotFoundError()
        active_role_count = await self._projects.count_active_by_company(company_id)
        total_hires = await self._candidates.count_by_statuses(
            company_id, {CandidateStatus.HIRED.value}
        )
        candidates_in_pipeline = await self._candidates.count_by_statuses(
            company_id, _IN_PROCESS_CANDIDATE_STATUSES
        )
        return ProfileStats(
            active_role_count=active_role_count,
            total_hires=total_hires,
            team_size=company.employee_count,
            candidates_in_pipeline=candidates_in_pipeline,
        )

    async def upload_logo(self, *, actor: User, content: bytes, content_type: str) -> Company:
        return await self._upload_media(
            actor=actor, content=content, content_type=content_type, field="logo_storage_key"
        )

    async def upload_cover_image(
        self, *, actor: User, content: bytes, content_type: str
    ) -> Company:
        return await self._upload_media(
            actor=actor,
            content=content,
            content_type=content_type,
            field="cover_image_storage_key",
        )

    async def _upload_media(
        self, *, actor: User, content: bytes, content_type: str, field: str
    ) -> Company:
        assert self._storage is not None, "CompanyService needs storage= for media uploads"
        extension = _ALLOWED_IMAGE_CONTENT_TYPES.get(content_type)
        if extension is None:
            raise InvalidMediaFileError("Image must be PNG, JPEG, or WebP — got: " + content_type)
        max_bytes = self._settings.max_media_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise InvalidMediaFileError(
                f"Image exceeds the {self._settings.max_media_size_mb}MB limit"
            )

        company = await self._repository.get_by_id(actor.company_id)
        if company is None:
            raise CompanyNotFoundError()

        label = "logo" if field == "logo_storage_key" else "cover"
        key = f"{actor.company_id}/{label}/{uuid.uuid4()}{extension}"
        await self._storage.save(key=key, content=content, content_type=content_type)

        old_key = getattr(company, field)
        setattr(company, field, key)
        if old_key is not None:
            await self._storage.delete(key=old_key)
        await self._session.flush()
        return company

    async def read_media(self, *, slug: str, field: str) -> tuple[bytes, str]:
        assert self._storage is not None, "CompanyService needs storage= for media reads"
        company = await self._repository.get_by_slug(slug)
        key = getattr(company, field, None) if company is not None else None
        if company is None or key is None:
            raise CompanyNotFoundError()
        content = await self._storage.read(key=key)
        extension = key.rsplit(".", 1)[-1]
        content_type = next(
            (ct for ct, ext in _ALLOWED_IMAGE_CONTENT_TYPES.items() if ext == f".{extension}"),
            "application/octet-stream",
        )
        return content, content_type

    async def preview_profile(self, *, actor_company_id: uuid.UUID) -> CompanyProfileRead:
        company = await self._repository.get_by_id(actor_company_id)
        if company is None:
            raise CompanyNotFoundError()
        return self._draft_to_profile_read(company)

    # --- Self-service: publish-state transitions -------------------------------------------------

    async def submit_for_review(self, *, actor: User) -> Company:
        company = await self._repository.get_by_id(actor.company_id)
        if company is None:
            raise CompanyNotFoundError()
        if company.profile_status not in _SUBMITTABLE_STATUSES:
            raise InvalidProfileTransitionError()
        company.profile_status = CompanyProfileStatus.PENDING_REVIEW.value
        await self._session.flush()
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="company.profile_submitted_for_review",
            target_type="company",
            target_id=company.id,
        )
        return company

    async def pause_profile(self, *, actor: User) -> Company:
        return await self._toggle_pause(actor=actor, target=CompanyProfileStatus.PAUSED)

    async def resume_profile(self, *, actor: User) -> Company:
        return await self._toggle_pause(actor=actor, target=CompanyProfileStatus.LIVE)

    async def _toggle_pause(self, *, actor: User, target: CompanyProfileStatus) -> Company:
        company = await self._repository.get_by_id(actor.company_id)
        if company is None:
            raise CompanyNotFoundError()
        source = (
            CompanyProfileStatus.LIVE
            if target == CompanyProfileStatus.PAUSED
            else CompanyProfileStatus.PAUSED
        )
        if company.profile_status != source.value:
            raise InvalidProfileTransitionError()
        company.profile_status = target.value
        await self._session.flush()
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action=f"company.profile_{target.value}",
            target_type="company",
            target_id=company.id,
        )
        return company

    # --- Public --------------------------------------------------------------------------------

    async def get_public_profile(self, slug: str) -> CompanyProfileRead | None:
        company = await self._repository.get_by_slug(slug)
        if (
            company is None
            or company.deleted_at is not None
            or not is_profile_publicly_visible(company)
            or company.current_profile_version_id is None
        ):
            return None
        version = await self._versions.get_by_id(company.current_profile_version_id)
        if version is None:
            return None
        profile = CompanyProfileRead.model_validate(version.snapshot)
        # is_verified_employer is deliberately read live, not frozen into the snapshot -- it's an
        # admin action independent of the company's own draft/review cycle, and a company
        # shouldn't have to resubmit their profile for the verified badge to appear or disappear.
        return profile.model_copy(update={"is_verified_employer": company.is_verified_employer})

    # --- Admin: profile review queue ------------------------------------------------------------

    async def list_companies_with_user_counts(
        self, *, profile_status: str | None = None
    ) -> list[tuple[Company, int]]:
        companies = await self._repository.list_all(profile_status=profile_status)
        return [(company, await self._users.count_by_company(company.id)) for company in companies]

    async def approve_profile_review(
        self, *, admin_id: uuid.UUID, company_id: uuid.UUID
    ) -> Company:
        company = await self._repository.get_by_id(company_id)
        if company is None:
            raise CompanyNotFoundError()
        if company.profile_status != CompanyProfileStatus.PENDING_REVIEW.value:
            raise InvalidProfileTransitionError()

        next_version_number = await self._versions.get_latest_version_number(company.id) + 1
        snapshot = self._draft_to_profile_read(company).model_dump(mode="json")
        version = await self._versions.create(
            company_id=company.id,
            version_number=next_version_number,
            snapshot=snapshot,
            approved_by_admin_id=admin_id,
        )
        company.current_profile_version_id = version.id
        company.profile_status = CompanyProfileStatus.LIVE.value
        await self._session.flush()
        await self._platform_audit.record(
            admin_id=admin_id,
            action="company_profile.approved",
            target_type="company",
            target_id=company.id,
            extra_data={"company_name": company.name, "version_number": next_version_number},
        )
        if self._email_sender is not None:
            profile_url = f"{self._settings.frontend_base_url}/shadow/companies/{company.slug}"
            subject, body = build_profile_approved_email(
                company_name=company.name, profile_url=profile_url
            )
            await self._notify_company_users(company.id, subject=subject, body=body)
        return company

    async def reject_profile_review(
        self, *, admin_id: uuid.UUID, company_id: uuid.UUID, reason: str | None
    ) -> Company:
        company = await self._repository.get_by_id(company_id)
        if company is None:
            raise CompanyNotFoundError()
        if company.profile_status != CompanyProfileStatus.PENDING_REVIEW.value:
            raise InvalidProfileTransitionError()
        company.profile_status = CompanyProfileStatus.DRAFT.value
        await self._session.flush()
        await self._platform_audit.record(
            admin_id=admin_id,
            action="company_profile.rejected",
            target_type="company",
            target_id=company.id,
            extra_data={"company_name": company.name, "reason": reason},
        )
        if self._email_sender is not None:
            subject, body = build_profile_rejected_email(company_name=company.name, reason=reason)
            await self._notify_company_users(company.id, subject=subject, body=body)
        return company

    async def _notify_company_users(
        self, company_id: uuid.UUID, *, subject: str, body: str
    ) -> None:
        """Every active user on the company, not just one owner -- there's no single
        "who submitted this" field on Company, and any of them would want to know their
        profile's review outcome. Small scale (default limit=50) matches this codebase's
        general no-pagination-needed-yet acceptance elsewhere."""

        assert self._email_sender is not None
        users = await self._users.list_by_company(company_id)
        for user in users:
            await self._email_sender.send(to=user.email, subject=subject, body=body)

    # --- Admin: workspace suspension (unrelated to profile review) -------------------------------

    async def get_status_counts(self) -> dict[str, int]:
        counts = await self._repository.get_status_counts()
        return {
            "active_companies": counts.get(CompanyStatus.APPROVED.value, 0),
            "suspended_companies": counts.get(CompanyStatus.SUSPENDED.value, 0),
        }

    async def suspend_company(self, *, admin_id: uuid.UUID, company_id: uuid.UUID) -> Company:
        company = await self._repository.get_by_id(company_id)
        if company is None:
            raise CompanyNotFoundError()
        if company.status == CompanyStatus.SUSPENDED.value:
            raise CompanyAlreadyInStatusError()
        company.status = CompanyStatus.SUSPENDED.value
        await self._session.flush()
        await self._platform_audit.record(
            admin_id=admin_id,
            action="company.suspended",
            target_type="company",
            target_id=company.id,
            extra_data={"company_name": company.name},
        )
        return company

    async def reactivate_company(self, *, admin_id: uuid.UUID, company_id: uuid.UUID) -> Company:
        company = await self._repository.get_by_id(company_id)
        if company is None:
            raise CompanyNotFoundError()
        if company.status == CompanyStatus.APPROVED.value:
            raise CompanyAlreadyInStatusError()
        company.status = CompanyStatus.APPROVED.value
        await self._session.flush()
        await self._platform_audit.record(
            admin_id=admin_id,
            action="company.reactivated",
            target_type="company",
            target_id=company.id,
            extra_data={"company_name": company.name},
        )
        return company

    # --- Shared helpers ------------------------------------------------------------------------

    def to_read(self, company: Company) -> CompanyRead:
        return CompanyRead(
            id=company.id,
            name=company.name,
            slug=company.slug,
            email_domain=company.email_domain,
            is_verified_domain=company.is_verified_domain,
            description=company.description,
            culture=company.culture,
            benefits=company.benefits,
            size=company.size,
            industry=company.industry,
            logo_url=self._media_url(company.slug, "logo", company.logo_storage_key),
            cover_image_url=self._media_url(
                company.slug, "cover-image", company.cover_image_storage_key
            ),
            hiring_process_overview=company.hiring_process_overview,
            profile_status=company.profile_status,
            status=company.status,
            tagline=company.tagline,
            website=company.website,
            founded_year=company.founded_year,
            headquarters=company.headquarters,
            employee_count=company.employee_count,
            is_verified_employer=company.is_verified_employer,
            values=company.values,
            looking_for=company.looking_for,
            hiring_highlights=company.hiring_highlights,
        )

    def _draft_to_profile_read(self, company: Company) -> CompanyProfileRead:
        return CompanyProfileRead(
            name=company.name,
            slug=company.slug,
            description=company.description,
            culture=company.culture,
            benefits=company.benefits,
            size=company.size,
            industry=company.industry,
            logo_url=self._media_url(company.slug, "logo", company.logo_storage_key),
            cover_image_url=self._media_url(
                company.slug, "cover-image", company.cover_image_storage_key
            ),
            hiring_process_overview=company.hiring_process_overview,
            tagline=company.tagline,
            website=company.website,
            founded_year=company.founded_year,
            headquarters=company.headquarters,
            is_verified_employer=company.is_verified_employer,
            values=company.values,
            looking_for=company.looking_for,
            hiring_highlights=company.hiring_highlights,
        )

    @staticmethod
    def _media_url(slug: str, kind: str, storage_key: str | None) -> str | None:
        if storage_key is None:
            return None
        return f"/api/v1/companies/{slug}/{kind}"
