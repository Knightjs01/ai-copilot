import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.historic_vault.models import PurgedProjectRecord

# A company's purge/audit history is at most a few hundred/thousand rows in practice — same
# unpaginated-read reasoning used by analytics.service and dashboard.service.
_MAX_PURGED_PROJECTS = 500
_MAX_AUDIT_ENTRIES = 200


class HistoricVaultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        project_id: uuid.UUID,
        project_title: str,
        candidate_count: int,
        data_categories_destroyed: list[str],
        purged_by_email: str,
        purged_at: datetime,
    ) -> PurgedProjectRecord:
        record = PurgedProjectRecord(
            company_id=company_id,
            project_id=project_id,
            project_title=project_title,
            candidate_count=candidate_count,
            data_categories_destroyed=data_categories_destroyed,
            purged_by_email=purged_by_email,
            purged_at=purged_at,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def list_purged_projects_by_company(
        self, company_id: uuid.UUID
    ) -> list[PurgedProjectRecord]:
        result = await self._session.execute(
            select(PurgedProjectRecord)
            .where(PurgedProjectRecord.company_id == company_id)
            .order_by(PurgedProjectRecord.purged_at.desc())
            .limit(_MAX_PURGED_PROJECTS)
        )
        return list(result.scalars().all())

    async def list_recent_audit_entries_by_company(
        self, company_id: uuid.UUID
    ) -> list[tuple[AuditLog, str | None]]:
        """Left-joins the actor's current email — a null actor_user_id (system-triggered rows) or
        a since-removed user both fall back to None, which the API layer renders as "System"."""
        result = await self._session.execute(
            select(AuditLog, User.email)
            .outerjoin(User, User.id == AuditLog.actor_user_id)
            .where(AuditLog.company_id == company_id)
            .order_by(AuditLog.created_at.desc())
            .limit(_MAX_AUDIT_ENTRIES)
        )
        return [(row[0], row[1]) for row in result.all()]
