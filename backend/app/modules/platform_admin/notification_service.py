import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.platform_admin.models import PlatformAdminNotification
from app.modules.platform_admin.notification_repository import PlatformAdminNotificationRepository
from app.modules.platform_admin.repository import PlatformAdminRepository


class PlatformAdminNotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self._notifications = PlatformAdminNotificationRepository(session)
        self._admins = PlatformAdminRepository(session)

    async def notify(
        self,
        *,
        action: str,
        title: str,
        body: str,
        target_type: str,
        target_id: uuid.UUID | None = None,
        required_permission: str | None = None,
    ) -> None:
        await self._notifications.create(
            action=action,
            title=title,
            body=body,
            target_type=target_type,
            target_id=target_id,
            required_permission=required_permission,
        )

    async def list_visible(
        self, *, permissions: set[str], limit: int = 20, offset: int = 0
    ) -> list[PlatformAdminNotification]:
        return await self._notifications.list_visible(
            permissions=permissions, limit=limit, offset=offset
        )

    async def count_visible(self, *, permissions: set[str]) -> int:
        return await self._notifications.count_visible(permissions=permissions)

    async def get_unread_count(self, *, admin_id: uuid.UUID, permissions: set[str]) -> int:
        admin = await self._admins.get_by_id(admin_id)
        if admin is None:
            return 0
        return await self._notifications.count_unread(
            permissions=permissions, since=admin.notifications_read_at
        )

    async def mark_read(self, *, admin_id: uuid.UUID) -> None:
        await self._admins.mark_notifications_read(admin_id)
