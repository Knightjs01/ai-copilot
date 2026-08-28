import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.audit.schemas import AuditEntryRead
from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user_model,
    get_email_sender,
    get_tenant_db,
    require_mfa_enrolled,
    require_permission,
)
from app.modules.auth.email import EmailSender
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.candidate_auth.dependencies import (
    require_candidate_mfa_enrolled,
    require_verified_candidate,
)
from app.modules.candidate_auth.models import CandidateUser
from app.modules.companies.dependencies import require_verified_domain
from app.modules.shadow_jobs.exceptions import ShadowJobNotFoundError
from app.modules.shadow_jobs.models import ShadowJob
from app.modules.shadow_jobs.repository import ShadowJobRepository
from app.modules.shadow_jobs.schemas import (
    AddFromTalentPoolRequest,
    JobIntelligence,
    ShadowApplicantPipelineUpdate,
    ShadowApplicationRead,
    ShadowJobBoardListing,
    ShadowJobCreate,
    ShadowJobRead,
    ShadowJobUpdate,
    ShadowProfile,
    ShadowProfileCompanyWide,
)
from app.modules.shadow_jobs.service import ShadowJobService

router = APIRouter(prefix="/shadow-jobs", tags=["shadow-jobs"])

# Nested project sub-resource lookup ("does this project have a linked Shadow Job") -- a separate
# APIRouter with its own /projects prefix, mirroring hiring_blueprint/api.py's exact pattern: a
# capability module owns its own routes even when nested under another resource's URL, rather
# than projects/api.py importing Shadow internals at the route layer.
project_router = APIRouter(
    prefix="/projects", tags=["shadow-jobs"], dependencies=[Depends(require_mfa_enrolled)]
)


async def _to_job_read(service: ShadowJobService, job: ShadowJob) -> ShadowJobRead:
    applicant_count = await service.get_applicant_count(job.id)
    read_model = ShadowJobRead.model_validate(job)
    read_model.applicant_count = applicant_count
    return read_model


# --- Company-side job management --------------------------------------------------------------


@router.post("", response_model=ShadowJobRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    body: ShadowJobCreate,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_CREATE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ShadowJobRead:
    service = ShadowJobService(session)
    job = await service.create_job(actor=actor, body=body)
    return await _to_job_read(service, job)


@router.get("/mine", response_model=list[ShadowJobRead])
async def list_my_company_jobs(
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ShadowJobRead]:
    service = ShadowJobService(session)
    jobs = await service.list_jobs_for_company(
        company_id=actor.company_id, limit=limit, offset=offset
    )
    return [await _to_job_read(service, job) for job in jobs]


@router.get("/mine/{job_id}", response_model=ShadowJobRead)
async def get_my_company_job(
    job_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ShadowJobRead:
    service = ShadowJobService(session)
    job = await service.get_job_for_company(company_id=actor.company_id, job_id=job_id)
    return await _to_job_read(service, job)


@router.patch("/mine/{job_id}", response_model=ShadowJobRead)
async def update_job(
    job_id: uuid.UUID,
    body: ShadowJobUpdate,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ShadowJobRead:
    service = ShadowJobService(session)
    job = await service.update_job(actor=actor, job_id=job_id, body=body)
    return await _to_job_read(service, job)


@router.post("/mine/{job_id}/publish", response_model=ShadowJobRead)
async def publish_job(
    job_id: uuid.UUID,
    actor: User = Depends(require_verified_domain),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ShadowJobRead:
    # Submits into the platform-admin review queue -- it does not go live yet (see
    # platform_admin/jobs_api.py's approve route, the actual publish + alert-notify moment).
    service = ShadowJobService(session)
    job = await service.submit_for_review(actor=actor, job_id=job_id)
    return await _to_job_read(service, job)


@router.post("/mine/{job_id}/close", response_model=ShadowJobRead)
async def close_job(
    job_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ShadowJobRead:
    service = ShadowJobService(session)
    job = await service.close_job(actor=actor, job_id=job_id)
    return await _to_job_read(service, job)


@router.get("/mine/{job_id}/applicants", response_model=list[ShadowProfile])
async def list_applicants(
    job_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[ShadowProfile]:
    return await ShadowJobService(session).list_applicants(
        company_id=actor.company_id, job_id=job_id
    )


@router.get("/mine/{job_id}/applicants/{application_id}", response_model=ShadowProfile)
async def get_applicant(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ShadowProfile:
    return await ShadowJobService(session).get_applicant(
        company_id=actor.company_id, job_id=job_id, application_id=application_id
    )


@router.get(
    "/mine/{job_id}/applicants/{application_id}/activity", response_model=list[AuditEntryRead]
)
async def list_applicant_activity(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[AuditEntryRead]:
    return await ShadowJobService(session).list_applicant_activity(
        actor=actor, job_id=job_id, application_id=application_id
    )


@router.get("/applicants/mine", response_model=list[ShadowProfileCompanyWide])
async def list_all_applicants_for_company(
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[ShadowProfileCompanyWide]:
    return await ShadowJobService(session).list_applicants_for_company(actor=actor)


@router.post(
    "/mine/{job_id}/applicants/add-from-talent-pool",
    response_model=ShadowApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_applicant_from_talent_pool(
    job_id: uuid.UUID,
    body: AddFromTalentPoolRequest,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> ShadowApplicationRead:
    return await ShadowJobService(session, email_sender=email_sender).apply_on_behalf(
        actor=actor, job_id=job_id, callsign=body.callsign
    )


@router.patch("/mine/{job_id}/applicants/{application_id}", response_model=ShadowProfile)
async def update_applicant_pipeline_stage(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    body: ShadowApplicantPipelineUpdate,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ShadowProfile:
    return await ShadowJobService(session).update_applicant_pipeline_stage(
        actor=actor,
        job_id=job_id,
        application_id=application_id,
        pipeline_stage=body.pipeline_stage.value,
    )


@router.post("/mine/{job_id}/applicants/{application_id}/mark-viewed", response_model=ShadowProfile)
async def mark_applicant_viewed(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ShadowProfile:
    return await ShadowJobService(session).mark_applicant_viewed(
        actor=actor, job_id=job_id, application_id=application_id
    )


# --- Public job board ----------------------------------------------------------------------


@router.get("/board", response_model=list[ShadowJobBoardListing])
async def browse_board(
    session: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    seniority: str | None = None,
    remote_preference: str | None = None,
    employment_type: str | None = None,
    location: str | None = None,
) -> list[ShadowJobBoardListing]:
    return await ShadowJobService(session).browse_board(
        limit=limit,
        offset=offset,
        seniority=seniority,
        remote_preference=remote_preference,
        employment_type=employment_type,
        location=location,
    )


@router.get("/board/{job_id}", response_model=ShadowJobBoardListing)
async def get_board_job(
    job_id: uuid.UUID, session: AsyncSession = Depends(get_db)
) -> ShadowJobBoardListing:
    return await ShadowJobService(session).get_board_detail(job_id)


@router.get("/board/{job_id}/intelligence", response_model=JobIntelligence)
async def get_job_intelligence(
    job_id: uuid.UUID, session: AsyncSession = Depends(get_db)
) -> JobIntelligence:
    return await ShadowJobService(session).get_job_intelligence(job_id)


# --- Apply with Phantom Passport (candidate-authenticated) ---------------------------------


@router.post(
    "/board/{job_id}/apply",
    response_model=ShadowApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
async def apply_to_job(
    job_id: uuid.UUID,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    _: CandidateUser = Depends(require_verified_candidate),
    session: AsyncSession = Depends(get_db),
) -> ShadowApplicationRead:
    return await ShadowJobService(session).apply(candidate=candidate, job_id=job_id)


@router.get("/applications/me", response_model=list[ShadowApplicationRead])
async def list_my_applications(
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> list[ShadowApplicationRead]:
    return await ShadowJobService(session).list_my_applications(candidate=candidate)


@router.get("/applications/me/{application_id}", response_model=ShadowApplicationRead)
async def get_my_application(
    application_id: uuid.UUID,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> ShadowApplicationRead:
    return await ShadowJobService(session).get_my_application(
        candidate=candidate, application_id=application_id
    )


@router.post("/applications/me/{application_id}/withdraw", response_model=ShadowApplicationRead)
async def withdraw_application(
    application_id: uuid.UUID,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> ShadowApplicationRead:
    return await ShadowJobService(session).withdraw_application(
        candidate=candidate, application_id=application_id
    )


# --- Project sub-resource: "does this project have a linked Shadow Job" --------------------


@project_router.get("/{project_id}/shadow-job", response_model=ShadowJobRead)
async def get_project_shadow_job(
    project_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ShadowJobRead:
    service = ShadowJobService(session)
    job = await ShadowJobRepository(session).get_by_project_id(project_id)
    if job is None or job.company_id != actor.company_id:
        raise ShadowJobNotFoundError()
    return await _to_job_read(service, job)


@project_router.post("/{project_id}/shadow-job", response_model=ShadowJobRead)
async def publish_project_to_shadow(
    project_id: uuid.UUID,
    body: ShadowJobCreate,
    actor: User = Depends(require_verified_domain),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_CREATE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ShadowJobRead:
    # Submits into the platform-admin review queue -- see publish_job's comment above.
    service = ShadowJobService(session)
    job = await service.publish_project_to_shadow(actor=actor, project_id=project_id, body=body)
    return await _to_job_read(service, job)
