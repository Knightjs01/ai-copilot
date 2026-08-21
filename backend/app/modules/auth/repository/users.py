import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Role, User, UserRole


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        email: str,
        hashed_password: str | None,
        full_name: str,
        is_active: bool = True,
    ) -> User:
        user = User(
            company_id=company_id,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=is_active,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def list_by_company(
        self, company_id: uuid.UUID, *, limit: int = 50, offset: int = 0
    ) -> list[User]:
        result = await self._session.execute(
            select(User)
            .where(User.company_id == company_id, User.deleted_at.is_(None))
            .order_by(User.created_at)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_by_company(self, company_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(User)
            .where(User.company_id == company_id, User.deleted_at.is_(None))
        )
        return int(result.scalar_one())

    async def count_users_with_role(self, company_id: uuid.UUID, role_name: str) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(User)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                User.company_id == company_id,
                User.deleted_at.is_(None),
                Role.name == role_name,
            )
        )
        return int(result.scalar_one())
