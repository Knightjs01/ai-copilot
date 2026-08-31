import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.candidate_auth.dependencies import require_candidate_mfa_enrolled
from app.modules.candidate_auth.models import CandidateUser
from app.modules.dismissed_shadow_jobs.schemas import DismissedShadowJobCreate
from app.modules.dismissed_shadow_jobs.service import DismissedShadowJobService

router = APIRouter(prefix="/dismissed-jobs", tags=["dismissed-jobs"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def dismiss_job(
    body: DismissedShadowJobCreate,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> None:
    await DismissedShadowJobService(session).dismiss_job(
        candidate_user_id=candidate.id, shadow_job_id=body.shadow_job_id
    )


@router.get("", response_model=list[uuid.UUID])
async def list_dismissed_jobs(
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> list[uuid.UUID]:
    return await DismissedShadowJobService(session).list_dismissed_job_ids(candidate.id)


@router.delete("/{shadow_job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def undismiss_job(
    shadow_job_id: uuid.UUID,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> None:
    await DismissedShadowJobService(session).undismiss_job(
        candidate_user_id=candidate.id, shadow_job_id=shadow_job_id
    )
