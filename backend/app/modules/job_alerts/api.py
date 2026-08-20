import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.candidate_auth.dependencies import require_candidate_mfa_enrolled
from app.modules.candidate_auth.models import CandidateUser
from app.modules.job_alerts.schemas import JobAlertCreate, JobAlertRead, JobAlertUpdate
from app.modules.job_alerts.service import JobAlertService

router = APIRouter(prefix="/job-alerts", tags=["job-alerts"])


@router.post("", response_model=JobAlertRead, status_code=status.HTTP_201_CREATED)
async def create_job_alert(
    body: JobAlertCreate,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> JobAlertRead:
    return await JobAlertService(session).create_alert(candidate_user_id=candidate.id, body=body)


@router.get("", response_model=list[JobAlertRead])
async def list_job_alerts(
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> list[JobAlertRead]:
    return await JobAlertService(session).list_alerts(candidate.id)


@router.patch("/{alert_id}", response_model=JobAlertRead)
async def update_job_alert(
    alert_id: uuid.UUID,
    body: JobAlertUpdate,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> JobAlertRead:
    return await JobAlertService(session).update_alert(
        candidate_user_id=candidate.id, alert_id=alert_id, body=body
    )


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_alert(
    alert_id: uuid.UUID,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
) -> None:
    await JobAlertService(session).delete_alert(candidate_user_id=candidate.id, alert_id=alert_id)
