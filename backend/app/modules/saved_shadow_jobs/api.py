import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.candidate_auth.dependencies import require_candidate_mfa_enrolled
from app.modules.candidate_auth.models import CandidateUser
from app.modules.saved_shadow_jobs.schemas import (
    SavedShadowJobCreate,
    SavedShadowJobRead,
    SavedShadowJobUpdate,
)
from app.modules.saved_shadow_jobs.service import SavedShadowJobService

router = APIRouter(prefix="/saved-jobs", tags=["saved-jobs"])


@router.post("", response_model=SavedShadowJobRead, status_code=status.HTTP_201_CREATED)
async def save_job(
    body: SavedShadowJobCreate,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> SavedShadowJobRead:
    return await SavedShadowJobService(session).save_job(
        candidate_user_id=candidate.id,
        shadow_job_id=body.shadow_job_id,
        collection_name=body.collection_name,
    )


@router.get("", response_model=list[SavedShadowJobRead])
async def list_saved_jobs(
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
    collection_name: str | None = Query(default=None),
) -> list[SavedShadowJobRead]:
    return await SavedShadowJobService(session).list_saved(
        candidate_user_id=candidate.id, collection_name=collection_name
    )


@router.patch("/{shadow_job_id}", response_model=SavedShadowJobRead)
async def update_saved_job(
    shadow_job_id: uuid.UUID,
    body: SavedShadowJobUpdate,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> SavedShadowJobRead:
    return await SavedShadowJobService(session).update_collection(
        candidate_user_id=candidate.id,
        shadow_job_id=shadow_job_id,
        collection_name=body.collection_name,
    )


@router.delete("/{shadow_job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_job(
    shadow_job_id: uuid.UUID,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> None:
    await SavedShadowJobService(session).unsave_job(
        candidate_user_id=candidate.id, shadow_job_id=shadow_job_id
    )
