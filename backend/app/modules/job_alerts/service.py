import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.email import EmailSender, build_job_alert_email
from app.modules.candidate_auth.repository import CandidateUserRepository
from app.modules.job_alerts.exceptions import (
    AlertLimitExceededError,
    EmptyAlertCriteriaError,
    JobAlertNotFoundError,
)
from app.modules.job_alerts.models import JobAlert
from app.modules.job_alerts.repository import JobAlertRepository
from app.modules.job_alerts.schemas import JobAlertCreate, JobAlertRead, JobAlertUpdate
from app.modules.shadow_jobs.models import ShadowJob

logger = logging.getLogger("app.job_alerts.service")

_MAX_ALERTS_PER_CANDIDATE = 10
_CRITERIA_FIELDS = ("seniority", "remote_preference", "employment_type", "location")


def _has_criteria(
    seniority: str | None,
    remote_preference: str | None,
    employment_type: str | None,
    location: str | None,
) -> bool:
    return any((seniority, remote_preference, employment_type, location))


def _matches(alert: JobAlert, job: ShadowJob) -> bool:
    if alert.seniority is not None and alert.seniority != job.seniority:
        return False
    if alert.remote_preference is not None and alert.remote_preference != job.remote_preference:
        return False
    if alert.employment_type is not None and alert.employment_type != job.employment_type:
        return False
    if alert.location is not None and alert.location != job.location:
        return False
    return True


class JobAlertService:
    def __init__(self, session: AsyncSession, *, email_sender: EmailSender | None = None) -> None:
        self._session = session
        self._alerts = JobAlertRepository(session)
        self._candidates = CandidateUserRepository(session)
        self._email_sender = email_sender

    async def create_alert(
        self, *, candidate_user_id: uuid.UUID, body: JobAlertCreate
    ) -> JobAlertRead:
        if not _has_criteria(
            body.seniority, body.remote_preference, body.employment_type, body.location
        ):
            raise EmptyAlertCriteriaError()

        existing_count = await self._alerts.count_by_candidate(candidate_user_id)
        if existing_count >= _MAX_ALERTS_PER_CANDIDATE:
            raise AlertLimitExceededError()

        alert = await self._alerts.create(
            candidate_user_id=candidate_user_id,
            name=body.name,
            seniority=body.seniority,
            remote_preference=body.remote_preference,
            employment_type=body.employment_type,
            location=body.location,
        )
        return JobAlertRead.model_validate(alert, from_attributes=True)

    async def list_alerts(self, candidate_user_id: uuid.UUID) -> list[JobAlertRead]:
        alerts = await self._alerts.list_by_candidate(candidate_user_id)
        return [JobAlertRead.model_validate(a) for a in alerts]

    async def update_alert(
        self, *, candidate_user_id: uuid.UUID, alert_id: uuid.UUID, body: JobAlertUpdate
    ) -> JobAlertRead:
        alert = await self._alerts.get_by_id(alert_id)
        if alert is None or alert.candidate_user_id != candidate_user_id:
            raise JobAlertNotFoundError()

        for field in body.model_fields_set:
            setattr(alert, field, getattr(body, field))

        if not _has_criteria(
            alert.seniority, alert.remote_preference, alert.employment_type, alert.location
        ):
            raise EmptyAlertCriteriaError()

        await self._session.flush()
        return JobAlertRead.model_validate(alert, from_attributes=True)

    async def delete_alert(self, *, candidate_user_id: uuid.UUID, alert_id: uuid.UUID) -> None:
        alert = await self._alerts.get_by_id(alert_id)
        if alert is None or alert.candidate_user_id != candidate_user_id:
            raise JobAlertNotFoundError()
        await self._alerts.delete_by_id_and_candidate(
            alert_id=alert_id, candidate_user_id=candidate_user_id
        )

    async def notify_matching_alerts(self, job: ShadowJob) -> None:
        """Called synchronously right after a job is published (see shadow_jobs/api.py) -- no
        background job runner exists in this codebase, so this is the one real moment a "new
        matching job" notification can fire. Dedupes by candidate so someone with two overlapping
        alerts gets exactly one email per newly-published job, not one per matching alert."""
        if self._email_sender is None:
            return

        active_alerts = await self._alerts.list_active()
        matches_by_candidate: dict[uuid.UUID, list[str]] = {}
        for alert in active_alerts:
            if not _matches(alert, job):
                continue
            label = alert.name or "Job alert"
            matches_by_candidate.setdefault(alert.candidate_user_id, []).append(label)

        for candidate_user_id, alert_names in matches_by_candidate.items():
            candidate = await self._candidates.get_by_id(candidate_user_id)
            if candidate is None:
                continue
            subject, body = build_job_alert_email(job_title=job.title, alert_names=alert_names)
            try:
                await self._email_sender.send(to=candidate.email, subject=subject, body=body)
            except Exception:
                # A send failure must never fail the publish request it's riding along with.
                logger.exception(
                    "Failed to send job alert email to candidate %s for job %s",
                    candidate_user_id,
                    job.id,
                )
