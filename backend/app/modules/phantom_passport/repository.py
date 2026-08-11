import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.phantom_passport.models import (
    PassportCareerEntry,
    PassportPersonalInfo,
    PhantomPassport,
)


class PhantomPassportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_candidate_user_id(
        self, candidate_user_id: uuid.UUID
    ) -> PhantomPassport | None:
        result = await self._session.execute(
            select(PhantomPassport).where(
                PhantomPassport.candidate_user_id == candidate_user_id,
                PhantomPassport.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        candidate_user_id: uuid.UUID,
        headline: str | None,
        seniority: str | None,
        years_experience: int | None,
        summary: str | None,
        skills: list[Any],
        industries: list[Any],
        location: str | None,
        remote_preference: str | None,
        salary_min: int | None,
        salary_max: int | None,
        notice_period: str | None,
        career_intent: str,
    ) -> PhantomPassport:
        existing = await self.get_by_candidate_user_id(candidate_user_id)
        if existing is not None:
            existing.headline = headline
            existing.seniority = seniority
            existing.years_experience = years_experience
            existing.summary = summary
            existing.skills = skills
            existing.industries = industries
            existing.location = location
            existing.remote_preference = remote_preference
            existing.salary_min = salary_min
            existing.salary_max = salary_max
            existing.notice_period = notice_period
            existing.career_intent = career_intent
            await self._session.flush()
            return existing

        passport = PhantomPassport(
            candidate_user_id=candidate_user_id,
            headline=headline,
            seniority=seniority,
            years_experience=years_experience,
            summary=summary,
            skills=skills,
            industries=industries,
            location=location,
            remote_preference=remote_preference,
            salary_min=salary_min,
            salary_max=salary_max,
            notice_period=notice_period,
            career_intent=career_intent,
        )
        self._session.add(passport)
        await self._session.flush()
        return passport


class PassportPersonalInfoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_passport_id(self, passport_id: uuid.UUID) -> PassportPersonalInfo | None:
        result = await self._session.execute(
            select(PassportPersonalInfo).where(PassportPersonalInfo.passport_id == passport_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        passport_id: uuid.UUID,
        legal_name_encrypted: str,
        phone_encrypted: str | None,
        address_encrypted: str | None,
    ) -> PassportPersonalInfo:
        existing = await self.get_by_passport_id(passport_id)
        if existing is not None:
            existing.legal_name_encrypted = legal_name_encrypted
            existing.phone_encrypted = phone_encrypted
            existing.address_encrypted = address_encrypted
            await self._session.flush()
            return existing

        info = PassportPersonalInfo(
            passport_id=passport_id,
            legal_name_encrypted=legal_name_encrypted,
            phone_encrypted=phone_encrypted,
            address_encrypted=address_encrypted,
        )
        self._session.add(info)
        await self._session.flush()
        return info


class PassportCareerEntryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_passport_id(self, passport_id: uuid.UUID) -> list[PassportCareerEntry]:
        result = await self._session.execute(
            select(PassportCareerEntry)
            .where(PassportCareerEntry.passport_id == passport_id)
            .order_by(PassportCareerEntry.display_order)
        )
        return list(result.scalars().all())

    async def replace_all(
        self, *, passport_id: uuid.UUID, entries: list[dict[str, Any]]
    ) -> list[PassportCareerEntry]:
        """Full replace — simplest correct semantics for a "save my career history" form where
        the candidate can reorder, add, or remove entries freely; there's no stable client-side
        id to diff against for entries that only exist as a CV-parse preview."""

        await self._session.execute(
            delete(PassportCareerEntry).where(PassportCareerEntry.passport_id == passport_id)
        )
        created = []
        for index, entry in enumerate(entries):
            row = PassportCareerEntry(passport_id=passport_id, display_order=index, **entry)
            self._session.add(row)
            created.append(row)
        await self._session.flush()
        return created
