import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.commercial.models import CommercialPlan


class CommercialPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, plan_id: uuid.UUID) -> CommercialPlan | None:
        return await self._session.get(CommercialPlan, plan_id)

    async def get_by_code(self, code: str) -> CommercialPlan | None:
        result = await self._session.execute(
            select(CommercialPlan).where(CommercialPlan.code == code)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[CommercialPlan]:
        result = await self._session.execute(
            select(CommercialPlan).where(CommercialPlan.is_active.is_(True)).order_by(
                CommercialPlan.monthly_price_pence
            )
        )
        return list(result.scalars().all())
