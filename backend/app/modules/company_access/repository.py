import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company_access.models import AccessRequestStatus, CompanyAccessRequest


class CompanyAccessRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        full_name: str,
        job_title: str | None,
        company_name: str,
        work_email: str,
        hashed_password: str,
    ) -> CompanyAccessRequest:
        request = CompanyAccessRequest(
            full_name=full_name,
            job_title=job_title,
            company_name=company_name,
            work_email=work_email,
            hashed_password=hashed_password,
        )
        self._session.add(request)
        await self._session.flush()
        return request

    async def get_by_id(self, request_id: uuid.UUID) -> CompanyAccessRequest | None:
        return await self._session.get(CompanyAccessRequest, request_id)

    async def get_by_work_email(self, work_email: str) -> CompanyAccessRequest | None:
        result = await self._session.execute(
            select(CompanyAccessRequest).where(CompanyAccessRequest.work_email == work_email)
        )
        return result.scalar_one_or_none()

    async def list_by_status(self, status: str | None) -> list[CompanyAccessRequest]:
        query = select(CompanyAccessRequest)
        if status is not None and status != "all":
            query = query.where(CompanyAccessRequest.status == status)
        query = query.order_by(CompanyAccessRequest.created_at.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_stats(self) -> dict[str, int]:
        result = await self._session.execute(
            select(CompanyAccessRequest.status, func.count()).group_by(CompanyAccessRequest.status)
        )
        counts = {status: count for status, count in result.all()}
        return {
            "pending_requests": counts.get(AccessRequestStatus.PENDING.value, 0),
            "approved_requests": counts.get(AccessRequestStatus.APPROVED.value, 0),
            "rejected_requests": counts.get(AccessRequestStatus.REJECTED.value, 0),
        }
