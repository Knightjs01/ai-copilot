import uuid
from datetime import date, datetime, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.talent_pool.models import TalentPoolGrant, TalentPoolGrantStatus, TalentPoolScope

_ACTIVE_STATUSES = (TalentPoolGrantStatus.REQUESTED.value, TalentPoolGrantStatus.GRANTED.value)


class TalentPoolGrantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        candidate_user_id: uuid.UUID,
        company_id: uuid.UUID,
        source_shadow_application_id: uuid.UUID | None,
        source_project_id: uuid.UUID | None,
        source_role_title: str,
        requested_by_user_id: uuid.UUID,
        note: str | None,
    ) -> TalentPoolGrant:
        grant = TalentPoolGrant(
            candidate_user_id=candidate_user_id,
            company_id=company_id,
            source_shadow_application_id=source_shadow_application_id,
            source_project_id=source_project_id,
            source_role_title=source_role_title,
            requested_by_user_id=requested_by_user_id,
            note=note,
        )
        self._session.add(grant)
        await self._session.flush()
        return grant

    async def get_by_id(self, grant_id: uuid.UUID) -> TalentPoolGrant | None:
        return await self._session.get(TalentPoolGrant, grant_id)

    async def get_active_by_pair(
        self, *, candidate_user_id: uuid.UUID, company_id: uuid.UUID
    ) -> TalentPoolGrant | None:
        """Powers the duplicate-request check — a non-terminal (requested/granted) row already
        exists for this pair. Mirrors the partial unique index in migration 0046."""
        result = await self._session.execute(
            select(TalentPoolGrant).where(
                TalentPoolGrant.candidate_user_id == candidate_user_id,
                TalentPoolGrant.company_id == company_id,
                TalentPoolGrant.status.in_(_ACTIVE_STATUSES),
            )
        )
        return result.scalar_one_or_none()

    async def list_latest_by_company_and_candidates(
        self, *, company_id: uuid.UUID, candidate_user_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, TalentPoolGrant]:
        """One grant per candidate at this company -- the most recently created row, so a
        candidate with a terminal (declined/withdrawn) row followed by a later active one shows
        the current state, not stale history. Powers ShadowProfile.talent_pool_status's bulk
        lookup (see shadow_jobs/service.py), same shape as _unread_counts_for_applications."""
        if not candidate_user_ids:
            return {}
        result = await self._session.execute(
            select(TalentPoolGrant)
            .where(
                TalentPoolGrant.company_id == company_id,
                TalentPoolGrant.candidate_user_id.in_(candidate_user_ids),
            )
            .order_by(TalentPoolGrant.created_at.desc())
        )
        latest: dict[uuid.UUID, TalentPoolGrant] = {}
        for grant in result.scalars().all():
            latest.setdefault(grant.candidate_user_id, grant)
        return latest

    async def list_eligible_for_job(
        self, *, company_id: uuid.UUID, project_id: uuid.UUID | None
    ) -> list[TalentPoolGrant]:
        """Which granted candidates a NEW job at this company may be matched against -- powers
        PassportMatchingService.search_talent_pool_for_job. company_wide grants are always
        eligible; project_only grants are eligible only when the new job is linked to the same
        project the original request came from. Written as an explicit branch (not relying on
        SQL NULL = NULL semantics) when the new job has no project_id -- a project-less job never
        matches any project_only grant, full stop."""
        if project_id is not None:
            scope_condition = or_(
                TalentPoolGrant.scope == TalentPoolScope.COMPANY_WIDE.value,
                and_(
                    TalentPoolGrant.scope == TalentPoolScope.PROJECT_ONLY.value,
                    TalentPoolGrant.source_project_id == project_id,
                ),
            )
        else:
            scope_condition = TalentPoolGrant.scope == TalentPoolScope.COMPANY_WIDE.value

        result = await self._session.execute(
            select(TalentPoolGrant).where(
                TalentPoolGrant.company_id == company_id,
                TalentPoolGrant.status == TalentPoolGrantStatus.GRANTED.value,
                scope_condition,
            )
        )
        return list(result.scalars().all())

    async def get_granted_eligible_for_project(
        self, *, candidate_user_id: uuid.UUID, company_id: uuid.UUID, project_id: uuid.UUID | None
    ) -> TalentPoolGrant | None:
        """Single-candidate version of list_eligible_for_job's scope check -- powers apply-on-
        behalf eligibility (ShadowJobService.apply_on_behalf): may this specific granted candidate
        be attached to a role at this project without a fresh consent request?"""
        if project_id is not None:
            scope_condition = or_(
                TalentPoolGrant.scope == TalentPoolScope.COMPANY_WIDE.value,
                and_(
                    TalentPoolGrant.scope == TalentPoolScope.PROJECT_ONLY.value,
                    TalentPoolGrant.source_project_id == project_id,
                ),
            )
        else:
            scope_condition = TalentPoolGrant.scope == TalentPoolScope.COMPANY_WIDE.value

        result = await self._session.execute(
            select(TalentPoolGrant).where(
                TalentPoolGrant.candidate_user_id == candidate_user_id,
                TalentPoolGrant.company_id == company_id,
                TalentPoolGrant.status == TalentPoolGrantStatus.GRANTED.value,
                scope_condition,
            )
        )
        return result.scalars().first()

    async def list_granted_by_company_id(self, company_id: uuid.UUID) -> list[TalentPoolGrant]:
        result = await self._session.execute(
            select(TalentPoolGrant)
            .where(
                TalentPoolGrant.company_id == company_id,
                TalentPoolGrant.status == TalentPoolGrantStatus.GRANTED.value,
            )
            .order_by(TalentPoolGrant.responded_at.desc())
        )
        return list(result.scalars().all())

    async def list_granted_company_ids_by_candidate(
        self, candidate_user_id: uuid.UUID
    ) -> list[uuid.UUID]:
        """Which companies this candidate currently holds a granted Talent Pool relationship
        with -- powers PassportMatchingService.list_talent_pool_opportunities."""
        result = await self._session.execute(
            select(TalentPoolGrant.company_id).where(
                TalentPoolGrant.candidate_user_id == candidate_user_id,
                TalentPoolGrant.status == TalentPoolGrantStatus.GRANTED.value,
            )
        )
        return list(result.scalars().all())

    async def list_by_candidate_id(self, candidate_user_id: uuid.UUID) -> list[TalentPoolGrant]:
        result = await self._session.execute(
            select(TalentPoolGrant)
            .where(TalentPoolGrant.candidate_user_id == candidate_user_id)
            .order_by(TalentPoolGrant.created_at.desc())
        )
        return list(result.scalars().all())

    async def respond(
        self, grant: TalentPoolGrant, *, approve: bool, scope: str | None, review_date: date | None
    ) -> TalentPoolGrant:
        grant.status = (
            TalentPoolGrantStatus.GRANTED.value if approve else TalentPoolGrantStatus.DECLINED.value
        )
        grant.scope = scope if approve and scope else grant.scope
        grant.review_date = review_date if approve else None
        grant.responded_at = datetime.now(timezone.utc)
        await self._session.flush()
        return grant

    async def withdraw(self, grant: TalentPoolGrant) -> TalentPoolGrant:
        grant.status = TalentPoolGrantStatus.WITHDRAWN.value
        grant.withdrawn_at = datetime.now(timezone.utc)
        await self._session.flush()
        return grant

    async def get_many_by_ids_and_company(
        self, *, grant_ids: list[uuid.UUID], company_id: uuid.UUID
    ) -> list[TalentPoolGrant]:
        """Ownership-scoped lookup for the pool-assign/rename actions (Phase 4) -- callers must
        verify len(result) == len(grant_ids) themselves if they need every requested id to have
        actually resolved to a grant this company owns."""
        result = await self._session.execute(
            select(TalentPoolGrant).where(
                TalentPoolGrant.id.in_(grant_ids), TalentPoolGrant.company_id == company_id
            )
        )
        return list(result.scalars().all())

    async def rename_pool(self, *, company_id: uuid.UUID, old_name: str, new_name: str) -> int:
        """Bulk-renames every granted row in one pool -- a pool is just "rows sharing this
        string" (see TalentPoolGrant.pool_name's docstring), so renaming it is renaming every
        row, mirroring how SavedShadowJob.collection_name has no dedicated rename endpoint
        either. Returns the number of rows updated."""
        result = await self._session.execute(
            select(TalentPoolGrant).where(
                TalentPoolGrant.company_id == company_id,
                TalentPoolGrant.status == TalentPoolGrantStatus.GRANTED.value,
                TalentPoolGrant.pool_name == old_name,
            )
        )
        grants = list(result.scalars().all())
        for grant in grants:
            grant.pool_name = new_name
        await self._session.flush()
        return len(grants)
