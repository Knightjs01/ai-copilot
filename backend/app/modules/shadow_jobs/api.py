import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user_model,
    get_tenant_db,
    require_permission,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.candidate_auth.dependencies import get_current_candidate
from app.modules.candidate_auth.models import CandidateUser
from app.modules.shadow_jobs.models import ShadowJob
from app.modules.shadow_jobs.schemas import (
    ShadowApplicationRead,
    ShadowJobBoardListing,
    ShadowJobCreate,
    ShadowJobRead,
    ShadowJobUpdate,
    ShadowProfile,
)
from app.modules.shadow_jobs.service import ShadowJobService

router = APIRouter(prefix="/shadow-jobs", tags=["shadow-jobs"])


async def _to_job_read(service: ShadowJobService, job: ShadowJob) -> ShadowJobRead:
    applicant_count = await service.get_applicant_count(job.id)
    read_model = ShadowJobRead.model_validate(job)
    read_model.applicant_count = applicant_count
    return read_model


# --- Company-side job management --------------------------------------------------------------


@router.post("", response_model=ShadowJobRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    body: ShadowJobCreate,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_CREATE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ShadowJobRead:
    service = ShadowJobService(session)
    job = await service.create_job(actor=actor, body=body)
    return await _to_job_read(service, job)


@router.get("/mine", response_model=list[ShadowJobRead])
async def list_my_company_jobs(
    actor: User = Depends(get_current_user_model),
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
    actor: User = Depends(get_current_user_model),
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
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ShadowJobRead:
    service = ShadowJobService(session)
    job = await service.update_job(actor=actor, job_id=job_id, body=body)
    return await _to_job_read(service, job)


@router.post("/mine/{job_id}/publish", response_model=ShadowJobRead)
async def publish_job(
    job_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ShadowJobRead:
    service = ShadowJobService(session)
    job = await service.publish_job(actor=actor, job_id=job_id)
    return await _to_job_read(service, job)


@router.post("/mine/{job_id}/close", response_model=ShadowJobRead)
async def close_job(
    job_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ShadowJobRead:
    service = ShadowJobService(session)
    job = await service.close_job(actor=actor, job_id=job_id)
    return await _to_job_read(service, job)


@router.get("/mine/{job_id}/applicants", response_model=list[ShadowProfile])
async def list_applicants(
    job_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[ShadowProfile]:
    return await ShadowJobService(session).list_applicants(
        company_id=actor.company_id, job_id=job_id
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


# --- Apply with Phantom Passport (candidate-authenticated) ---------------------------------


@router.post(
    "/board/{job_id}/apply",
    response_model=ShadowApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
async def apply_to_job(
    job_id: uuid.UUID,
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> ShadowApplicationRead:
    return await ShadowJobService(session).apply(candidate=candidate, job_id=job_id)


@router.get("/applications/me", response_model=list[ShadowApplicationRead])
async def list_my_applications(
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> list[ShadowApplicationRead]:
    return await ShadowJobService(session).list_my_applications(candidate=candidate)


@router.get("/applications/me/{application_id}", response_model=ShadowApplicationRead)
async def get_my_application(
    application_id: uuid.UUID,
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> ShadowApplicationRead:
    return await ShadowJobService(session).get_my_application(
        candidate=candidate, application_id=application_id
    )


@router.post("/applications/me/{application_id}/withdraw", response_model=ShadowApplicationRead)
async def withdraw_application(
    application_id: uuid.UUID,
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> ShadowApplicationRead:
    return await ShadowJobService(session).withdraw_application(
        candidate=candidate, application_id=application_id
    )
