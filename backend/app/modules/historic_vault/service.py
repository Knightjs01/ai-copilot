import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.historic_vault.repository import HistoricVaultRepository
from app.modules.historic_vault.schemas import (
    AuditLogEntryRead,
    HistoricVaultOverview,
    PurgedProjectRecordRead,
)


class HistoricVaultService:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = HistoricVaultRepository(session)

    async def get_overview(self, *, company_id: uuid.UUID) -> HistoricVaultOverview:
        purged_projects = await self._repository.list_purged_projects_by_company(company_id)
        audit_rows = await self._repository.list_recent_audit_entries_by_company(company_id)

        return HistoricVaultOverview(
            purged_project_count=len(purged_projects),
            purged_projects=[
                PurgedProjectRecordRead.model_validate(record) for record in purged_projects
            ],
            recent_audit_entries=[
                AuditLogEntryRead(
                    id=entry.id,
                    actor_email=actor_email,
                    action=entry.action,
                    target_type=entry.target_type,
                    target_id=entry.target_id,
                    extra_data=entry.extra_data,
                    created_at=entry.created_at,
                )
                for entry, actor_email in audit_rows
            ],
        )
