import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.applicant_notes.schemas import ApplicantNoteCreate, ApplicantNoteRead
from app.modules.applicant_notes.service import ApplicantNoteService
from app.modules.auth.dependencies import (
    CurrentUser,
    get_tenant_db,
    require_mfa_enrolled,
    require_permission,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions

router = APIRouter(prefix="/shadow-jobs", tags=["applicant-notes"])


@router.get(
    "/mine/{job_id}/applicants/{application_id}/notes", response_model=list[ApplicantNoteRead]
)
async def list_applicant_notes(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[ApplicantNoteRead]:
    return await ApplicantNoteService(session).list_notes(
        actor=actor, job_id=job_id, application_id=application_id
    )


@router.post(
    "/mine/{job_id}/applicants/{application_id}/notes",
    response_model=ApplicantNoteRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_applicant_note(
    job_id: uuid.UUID,
    application_id: uuid.UUID,
    body: ApplicantNoteCreate,
    actor: User = Depends(require_mfa_enrolled),
    _: CurrentUser = Depends(require_permission(Permissions.SHADOW_JOBS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ApplicantNoteRead:
    return await ApplicantNoteService(session).add_note(
        actor=actor, job_id=job_id, application_id=application_id, body=body.body
    )
