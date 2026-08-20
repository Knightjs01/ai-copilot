import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.job_alerts.models import JobAlert


class JobAlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        candidate_user_id: uuid.UUID,
        name: str | None,
        seniority: str | None,
        remote_preference: str | None,
        employment_type: str | None,
        location: str | None,
    ) -> JobAlert:
        alert = JobAlert(
            candidate_user_id=candidate_user_id,
            name=name,
            seniority=seniority,
            remote_preference=remote_preference,
            employment_type=employment_type,
            location=location,
        )
        self._session.add(alert)
        await self._session.flush()
        return alert

    async def get_by_id(self, alert_id: uuid.UUID) -> JobAlert | None:
        return await self._session.get(JobAlert, alert_id)

    async def list_by_candidate(self, candidate_user_id: uuid.UUID) -> list[JobAlert]:
        result = await self._session.execute(
            select(JobAlert)
            .where(JobAlert.candidate_user_id == candidate_user_id)
            .order_by(JobAlert.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_by_candidate(self, candidate_user_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(JobAlert.id).where(JobAlert.candidate_user_id == candidate_user_id)
        )
        return len(result.scalars().all())

    async def list_active(self) -> list[JobAlert]:
        result = await self._session.execute(select(JobAlert).where(JobAlert.is_active.is_(True)))
        return list(result.scalars().all())

    async def delete_by_id_and_candidate(
        self, *, alert_id: uuid.UUID, candidate_user_id: uuid.UUID
    ) -> None:
        await self._session.execute(
            delete(JobAlert).where(
                JobAlert.id == alert_id, JobAlert.candidate_user_id == candidate_user_id
            )
        )
