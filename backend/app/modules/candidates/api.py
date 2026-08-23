import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.authorization import actor_has_org_wide_access
from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user_model,
    get_tenant_db,
    require_mfa_enrolled,
    require_permission,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.candidates.dependencies import get_file_storage, require_candidate_access
from app.modules.candidates.models import (
    Candidate,
    CandidateSource,
    CandidateStatus,
    NoticePeriod,
    PrescreenOutcome,
)
from app.modules.candidates.schemas import CandidateCreate, CandidateRead, CandidateUpdate
from app.modules.candidates.service import CandidateService
from app.modules.candidates.storage import FileStorage
from app.modules.identity_vault.repository import IdentityRevealEventRepository
from app.modules.projects.repository import ProjectMemberRepository

router = APIRouter(
    prefix="/candidates", tags=["candidates"], dependencies=[Depends(require_mfa_enrolled)]
)


def _to_candidate_read(candidate: Candidate, *, is_revealed: bool) -> CandidateRead:
    return CandidateRead(
        id=candidate.id,
        company_id=candidate.company_id,
        project_id=candidate.project_id,
        callsign=candidate.callsign,
        candidate_ref=candidate.candidate_ref,
        source=CandidateSource(candidate.source),
        status=CandidateStatus(candidate.status),
        resume_original_filename=candidate.resume_original_filename,
        interview_scheduled_at=candidate.interview_scheduled_at,
        prescreen_outcome=(
            PrescreenOutcome(candidate.prescreen_outcome) if candidate.prescreen_outcome else None
        ),
        prescreen_notes=candidate.prescreen_notes,
        expected_salary=candidate.expected_salary,
        agency_name=candidate.agency_name,
        notice_period=NoticePeriod(candidate.notice_period) if candidate.notice_period else None,
        created_by_id=candidate.created_by_id,
        is_revealed=is_revealed,
    )


async def _is_revealed(session: AsyncSession, candidate_id: uuid.UUID) -> bool:
    revealed = await IdentityRevealEventRepository(session).list_revealed_candidate_ids(
        [candidate_id]
    )
    return candidate_id in revealed


@router.post("", response_model=CandidateRead, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    body: CandidateCreate,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.CANDIDATES_CREATE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> CandidateRead:
    if not await actor_has_org_wide_access(session, actor.id):
        is_member = await ProjectMemberRepository(session).is_member(
            project_id=body.project_id, user_id=actor.id
        )
        if not is_member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    candidate = await CandidateService(session).create_candidate(
        actor=actor,
        project_id=body.project_id,
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        source=body.source,
        status=body.status,
    )
    # A brand-new candidate can't have any reveal events yet -- no lookup needed.
    return _to_candidate_read(candidate, is_revealed=False)


@router.get("", response_model=list[CandidateRead])
async def list_candidates(
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.CANDIDATES_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
    project_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[CandidateRead]:
    accessible_project_ids: list[uuid.UUID] | None = None
    if not await actor_has_org_wide_access(session, actor.id):
        members = ProjectMemberRepository(session)
        if project_id is not None:
            if not await members.is_member(project_id=project_id, user_id=actor.id):
                return []
        else:
            accessible_project_ids = await members.list_project_ids_for_user(actor.id)

    candidates = await CandidateService(session).list_candidates(
        company_id=actor.company_id,
        project_id=project_id,
        accessible_project_ids=accessible_project_ids,
        limit=limit,
        offset=offset,
    )
    revealed_ids = await IdentityRevealEventRepository(session).list_revealed_candidate_ids(
        [c.id for c in candidates]
    )
    return [_to_candidate_read(c, is_revealed=c.id in revealed_ids) for c in candidates]


@router.get("/{candidate_id}", response_model=CandidateRead)
async def get_candidate(
    candidate_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.CANDIDATES_VIEW)),
    __: None = Depends(require_candidate_access),
    session: AsyncSession = Depends(get_tenant_db),
) -> CandidateRead:
    candidate = await CandidateService(session).get_candidate(
        company_id=actor.company_id, candidate_id=candidate_id
    )
    return _to_candidate_read(candidate, is_revealed=await _is_revealed(session, candidate_id))


@router.patch("/{candidate_id}", response_model=CandidateRead)
async def update_candidate(
    candidate_id: uuid.UUID,
    body: CandidateUpdate,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.CANDIDATES_UPDATE)),
    __: None = Depends(require_candidate_access),
    session: AsyncSession = Depends(get_tenant_db),
) -> CandidateRead:
    candidate = await CandidateService(session).update_candidate(
        actor=actor,
        candidate_id=candidate_id,
        source=body.source,
        status=body.status,
        interview_scheduled_at=body.interview_scheduled_at,
        prescreen_outcome=body.prescreen_outcome,
        prescreen_notes=body.prescreen_notes,
        expected_salary=body.expected_salary,
        agency_name=body.agency_name,
        notice_period=body.notice_period,
    )
    return _to_candidate_read(candidate, is_revealed=await _is_revealed(session, candidate_id))


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate(
    candidate_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.CANDIDATES_DELETE)),
    __: None = Depends(require_candidate_access),
    session: AsyncSession = Depends(get_tenant_db),
) -> None:
    await CandidateService(session).delete_candidate(actor=actor, candidate_id=candidate_id)


@router.post("/{candidate_id}/resume", response_model=CandidateRead)
async def upload_resume(
    candidate_id: uuid.UUID,
    file: UploadFile = File(...),
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.CANDIDATES_UPDATE)),
    __: None = Depends(require_candidate_access),
    session: AsyncSession = Depends(get_tenant_db),
    storage: FileStorage = Depends(get_file_storage),
) -> CandidateRead:
    content = await file.read()
    candidate = await CandidateService(session, storage=storage).upload_resume(
        actor=actor,
        candidate_id=candidate_id,
        content=content,
        content_type=file.content_type or "application/octet-stream",
        original_filename=file.filename or "resume",
    )
    return _to_candidate_read(candidate, is_revealed=await _is_revealed(session, candidate_id))


@router.get("/{candidate_id}/resume")
async def download_resume(
    candidate_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.CANDIDATES_VIEW)),
    __: None = Depends(require_candidate_access),
    session: AsyncSession = Depends(get_tenant_db),
    storage: FileStorage = Depends(get_file_storage),
) -> Response:
    content, filename, _content_type = await CandidateService(
        session, storage=storage
    ).download_resume(company_id=actor.company_id, candidate_id=candidate_id)
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
