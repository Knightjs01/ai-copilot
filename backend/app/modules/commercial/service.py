import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.commercial.exceptions import CommercialPlanNotFoundError
from app.modules.commercial.models import CommercialPlan
from app.modules.commercial.repository import CommercialPlanRepository
from app.modules.commercial.schemas import CompanyCommercialSummary
from app.modules.companies.exceptions import CompanyNotFoundError
from app.modules.companies.models import Company
from app.modules.platform_admin.audit_service import PlatformAdminAuditService
from app.modules.projects.repository import ProjectRepository


class CommercialService:
    """Owns the plan catalog and a company's effective active-role limit. Reads/writes
    Company.commercial_plan_id/active_role_limit_override directly (the columns live on Company,
    same cross-module pattern shadow_jobs.service already uses to read Company for board
    listings) rather than duplicating company lookups into a second repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._plans = CommercialPlanRepository(session)
        self._projects = ProjectRepository(session)
        self._platform_audit = PlatformAdminAuditService(session)

    async def get_plan_catalog(self) -> list[CommercialPlan]:
        return await self._plans.list_active()

    async def get_effective_limit_by_company_id(self, company_id: uuid.UUID) -> int | None:
        company = await self._session.get(Company, company_id)
        if company is None:
            raise CompanyNotFoundError()
        return await self.get_effective_limit(company)

    async def get_effective_limit(self, company: Company) -> int | None:
        """None means unlimited -- either a Scale company with no override configured yet, or a
        plan whose own active_role_limit is null. Never silently blocks a company an admin
        hasn't configured, per the plan's own explicit instruction."""

        if company.active_role_limit_override is not None:
            return company.active_role_limit_override
        if company.commercial_plan_id is None:
            return None
        plan = await self._plans.get_by_id(company.commercial_plan_id)
        return plan.active_role_limit if plan is not None else None

    async def get_company_summary(self, company_id: uuid.UUID) -> CompanyCommercialSummary:
        company = await self._session.get(Company, company_id)
        if company is None:
            raise CompanyNotFoundError()
        plan = (
            await self._plans.get_by_id(company.commercial_plan_id)
            if company.commercial_plan_id is not None
            else None
        )
        active_role_count = await self._projects.count_active_by_company(company_id)
        effective_limit = await self.get_effective_limit(company)
        return CompanyCommercialSummary(
            plan=plan,  # type: ignore[arg-type]
            active_role_count=active_role_count,
            effective_limit=effective_limit,
        )

    async def set_company_commercial(
        self,
        *,
        admin_id: uuid.UUID,
        company_id: uuid.UUID,
        plan_code: str | None,
        plan_code_set: bool,
        active_role_limit_override: int | None,
        active_role_limit_override_set: bool,
        reason: str | None,
    ) -> Company:
        company = await self._session.get(Company, company_id)
        if company is None:
            raise CompanyNotFoundError()

        old_plan = (
            await self._plans.get_by_id(company.commercial_plan_id)
            if company.commercial_plan_id is not None
            else None
        )
        old_override = company.active_role_limit_override

        new_plan = old_plan
        if plan_code_set:
            if plan_code is None:
                raise CommercialPlanNotFoundError("A commercial plan code is required")
            new_plan = await self._plans.get_by_code(plan_code)
            if new_plan is None:
                raise CommercialPlanNotFoundError()
            company.commercial_plan_id = new_plan.id
        if active_role_limit_override_set:
            company.active_role_limit_override = active_role_limit_override

        await self._session.flush()
        await self._platform_audit.record(
            admin_id=admin_id,
            action="company.plan_changed",
            target_type="company",
            target_id=company.id,
            extra_data={
                "company_name": company.name,
                "old_plan_code": old_plan.code if old_plan else None,
                "new_plan_code": new_plan.code if new_plan else None,
                "old_limit_override": old_override,
                "new_limit_override": company.active_role_limit_override,
                "reason": reason,
            },
        )
        return company
