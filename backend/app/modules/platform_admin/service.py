from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth import security
from app.modules.auth.exceptions import InvalidCredentialsError
from app.modules.auth.login_throttle import LoginAttemptTracker
from app.modules.platform_admin.repository import PlatformAdminRepository


class PlatformAdminAuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._admins = PlatformAdminRepository(session)

    async def login(self, *, email: str, password: str) -> str:
        throttle = LoginAttemptTracker(realm="platform_admin")
        if await throttle.is_locked(email):
            raise InvalidCredentialsError()

        admin = await self._admins.get_by_email(email)
        if admin is None or not admin.is_active:
            await throttle.record_failure(email)
            raise InvalidCredentialsError()
        if not security.verify_password(password, admin.hashed_password):
            await throttle.record_failure(email)
            raise InvalidCredentialsError()

        await throttle.clear(email)
        return security.create_platform_admin_access_token(admin_id=admin.id)
