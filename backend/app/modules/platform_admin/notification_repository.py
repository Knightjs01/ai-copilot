import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.platform_admin.models import PlatformAdminNotification


def _visibility_clause(permissions: set[str]):  # type: ignore[no-untyped-def]
    return or_(
        PlatformAdminNotification.required_permission.is_(None),
        PlatformAdminNotification.required_permission.in_(permissions),
    )


class PlatformAdminNotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        action: str,
        title: str,
        body: str,
        target_type: str,
        target_id: uuid.UUID | None,
        required_permission: str | None,
    ) -> PlatformAdminNotification:
        notification = PlatformAdminNotification(
            action=action,
            title=title,
            body=body,
            target_type=target_type,
            target_id=target_id,
            required_permission=required_permission,
        )
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def list_visible(
        self, *, permissions: set[str], limit: int = 20, offset: int = 0
    ) -> list[PlatformAdminNotification]:
        result = await self._session.execute(
            select(PlatformAdminNotification)
            .where(_visibility_clause(permissions))
            .order_by(PlatformAdminNotification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_visible(self, *, permissions: set[str]) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(PlatformAdminNotification)
            .where(_visibility_clause(permissions))
        )
        return result.scalar_one()

    async def count_unread(self, *, permissions: set[str], since: datetime) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(PlatformAdminNotification)
            .where(_visibility_clause(permissions), PlatformAdminNotification.created_at > since)
        )
        return result.scalar_one()
