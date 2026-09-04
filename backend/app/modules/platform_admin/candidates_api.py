import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.companies.repository import CompanyRepository
from app.modules.phantom_passport.models import PhantomPassport
from app.modules.phantom_passport.service import PhantomPassportService
from app.modules.platform_admin.dependencies import (
    PlatformAdminContext,
    require_platform_admin_permission,
)
from app.modules.platform_admin.permissions import PlatformAdminPermissions
from app.modules.platform_admin.schemas import (
    AdminCandidateApplication,
    AdminCandidateCareerEntry,
    AdminCandidateDetail,
    AdminCandidateListResponse,
    AdminCandidateSummary,
)
from app.modules.shadow_jobs.repository import ShadowJobRepository

router = APIRouter(prefix="/platform-admin/candidates", tags=["platform-admin"])


def _to_summary(passport: PhantomPassport) -> AdminCandidateSummary:
    return AdminCandidateSummary(
        id=passport.id,
        callsign=passport.callsign,
        headline=passport.headline,
        seniority=passport.seniority,
        verification_status=passport.verification_status,
        visibility=passport.visibility,
        career_intent=passport.career_intent,
        created_at=passport.created_at,
    )


@router.get("", response_model=AdminCandidateListResponse)
async def list_candidates(
    verification_status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.CANDIDATES_VIEW)
    ),
    session: AsyncSession = Depends(get_db),
) -> AdminCandidateListResponse:
    service = PhantomPassportService(session)
    passports = await service.list_admin_candidates(
        verification_status=verification_status, search=search, limit=limit, offset=offset
    )
    total = await service.count_admin_candidates(
        verification_status=verification_status, search=search
    )
    items = [_to_summary(passport) for passport in passports]
    return AdminCandidateListResponse(items=items, total=total)


@router.get("/{passport_id}", response_model=AdminCandidateDetail)
async def get_candidate_detail(
    passport_id: uuid.UUID,
    _: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.CANDIDATES_VIEW)
    ),
    session: AsyncSession = Depends(get_db),
) -> AdminCandidateDetail:
    service = PhantomPassportService(session)
    passport, career_entries, applications = await service.get_admin_candidate_detail(
        passport_id
    )

    companies = CompanyRepository(session)
    jobs = ShadowJobRepository(session)
    admin_applications: list[AdminCandidateApplication] = []
    for application in applications:
        job = await jobs.get_by_id(application.shadow_job_id)
        company = await companies.get_by_id(application.company_id)
        admin_applications.append(
            AdminCandidateApplication(
                shadow_job_id=application.shadow_job_id,
                job_title=job.title if job is not None else "Unknown role",
                company_id=application.company_id,
                company_name=company.name if company is not None else "Unknown company",
                status=application.status,
                pipeline_stage=application.pipeline_stage,
                created_at=application.created_at,
            )
        )

    return AdminCandidateDetail(
        **_to_summary(passport).model_dump(),
        years_experience=passport.years_experience,
        summary=passport.summary,
        skills=passport.skills,
        industries=passport.industries,
        location=passport.location,
        remote_preference=passport.remote_preference,
        salary_min=passport.salary_min,
        salary_max=passport.salary_max,
        notice_period=passport.notice_period,
        career_entries=[
            AdminCandidateCareerEntry(
                title=entry.title,
                company_name_anonymized=entry.company_name_anonymized,
                start_date=entry.start_date,
                end_date=entry.end_date,
                is_current=entry.is_current,
                responsibilities=entry.responsibilities,
                achievements=list(entry.achievements),
            )
            for entry in career_entries
        ],
        applications=admin_applications,
    )
