import uuid
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.phantom_passport.models import (
    CandidateCvDocument,
    PassportCareerEntry,
    PassportPersonalInfo,
    PassportVersion,
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

    async def get_by_id(self, passport_id: uuid.UUID) -> PhantomPassport | None:
        return await self._session.get(PhantomPassport, passport_id)

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
        visibility: str,
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
            existing.visibility = visibility
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
            visibility=visibility,
        )
        self._session.add(passport)
        await self._session.flush()
        return passport

    async def list_discoverable_candidates(
        self,
        *,
        limit: int = 50,
        location: str | None = None,
        seniority: str | None = None,
        min_years_experience: int | None = None,
        skills: list[str] | None = None,
    ) -> list[PhantomPassport]:
        """The candidate pool for company-side search (passport_matching.service.
        search_candidates_for_job). visibility != PRIVATE, career_intent != NOT_LOOKING (checked
        regardless of visibility -- see PassportVisibility's docstring), and an approved version
        must exist (nothing to score without one). No real pagination yet -- see the module's
        Phase 5 plan for why a flat limit is an honest, documented simplification for now.

        location/seniority/min_years_experience/skills are optional pre-scoring filters (Phase 4)
        -- applied here, before search_candidates_for_job's per-candidate LLM scoring loop, so a
        narrower filter also means fewer LLM calls, not just a smaller result set. location and
        seniority are free-text columns with no enum/normalization guarantee, so they're matched
        case-insensitively as a substring, not an exact match, to avoid silently missing real
        data. skills has the same normalization problem in a JSONB array, so "candidate has every
        requested skill" is checked in Python after the SQL fetch rather than fighting JSONB
        containment semantics against unknown casing."""
        conditions = [
            PhantomPassport.visibility != "private",
            PhantomPassport.career_intent != "not_looking",
            PhantomPassport.current_version_id.is_not(None),
            PhantomPassport.deleted_at.is_(None),
        ]
        if location:
            conditions.append(PhantomPassport.location.ilike(f"%{location}%"))
        if seniority:
            conditions.append(PhantomPassport.seniority.ilike(f"%{seniority}%"))
        if min_years_experience is not None:
            conditions.append(PhantomPassport.years_experience >= min_years_experience)

        result = await self._session.execute(
            select(PhantomPassport)
            .where(*conditions)
            .order_by(PhantomPassport.updated_at.desc())
            .limit(limit)
        )
        candidates = list(result.scalars().all())

        if skills:
            required = {s.strip().lower() for s in skills if s.strip()}
            candidates = [
                c
                for c in candidates
                if required.issubset({str(s).strip().lower() for s in c.skills})
            ]

        return candidates

    async def set_current_version(
        self, passport: PhantomPassport, *, version_id: uuid.UUID
    ) -> PhantomPassport:
        passport.current_version_id = version_id
        await self._session.flush()
        return passport

    async def callsign_exists(self, callsign: str) -> bool:
        result = await self._session.execute(
            select(PhantomPassport.id).where(PhantomPassport.callsign == callsign)
        )
        return result.scalar_one_or_none() is not None

    async def get_by_callsign(self, callsign: str) -> PhantomPassport | None:
        result = await self._session.execute(
            select(PhantomPassport).where(
                PhantomPassport.callsign == callsign, PhantomPassport.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def set_callsign(self, passport: PhantomPassport, *, callsign: str) -> PhantomPassport:
        passport.callsign = callsign
        await self._session.flush()
        return passport

    async def set_visibility(
        self, passport: PhantomPassport, *, visibility: str
    ) -> PhantomPassport:
        passport.visibility = visibility
        await self._session.flush()
        return passport

    async def count_by_verification_status(self, status: str) -> int:
        result = await self._session.execute(
            select(func.count()).where(
                PhantomPassport.verification_status == status,
                PhantomPassport.deleted_at.is_(None),
            )
        )
        return result.scalar_one()


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
    ) -> PassportPersonalInfo:
        existing = await self.get_by_passport_id(passport_id)
        if existing is not None:
            existing.legal_name_encrypted = legal_name_encrypted
            existing.phone_encrypted = phone_encrypted
            await self._session.flush()
            return existing

        info = PassportPersonalInfo(
            passport_id=passport_id,
            legal_name_encrypted=legal_name_encrypted,
            phone_encrypted=phone_encrypted,
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


class CandidateCvDocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_candidate_user_id(
        self, candidate_user_id: uuid.UUID
    ) -> CandidateCvDocument | None:
        result = await self._session.execute(
            select(CandidateCvDocument).where(
                CandidateCvDocument.candidate_user_id == candidate_user_id
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        candidate_user_id: uuid.UUID,
        storage_key: str,
        original_filename: str,
        content_type: str,
        file_size: int,
    ) -> CandidateCvDocument:
        existing = await self.get_by_candidate_user_id(candidate_user_id)
        if existing is not None:
            existing.storage_key = storage_key
            existing.original_filename = original_filename
            existing.content_type = content_type
            existing.file_size = file_size
            await self._session.flush()
            return existing

        document = CandidateCvDocument(
            candidate_user_id=candidate_user_id,
            storage_key=storage_key,
            original_filename=original_filename,
            content_type=content_type,
            file_size=file_size,
        )
        self._session.add(document)
        await self._session.flush()
        return document

    async def delete(self, document: CandidateCvDocument) -> None:
        await self._session.delete(document)
        await self._session.flush()


class PassportVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, version_id: uuid.UUID) -> PassportVersion | None:
        return await self._session.get(PassportVersion, version_id)

    async def get_latest_version_number(self, passport_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(PassportVersion.version_number)
            .where(PassportVersion.passport_id == passport_id)
            .order_by(PassportVersion.version_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none() or 0

    async def create(
        self,
        *,
        passport_id: uuid.UUID,
        version_number: int,
        snapshot: dict[str, Any],
        source_cv_document_id: uuid.UUID | None,
        source_cv_filename: str | None,
    ) -> PassportVersion:
        version = PassportVersion(
            passport_id=passport_id,
            version_number=version_number,
            snapshot=snapshot,
            source_cv_document_id=source_cv_document_id,
            source_cv_filename=source_cv_filename,
        )
        self._session.add(version)
        await self._session.flush()
        return version

    async def list_by_passport_id(self, passport_id: uuid.UUID) -> list[PassportVersion]:
        result = await self._session.execute(
            select(PassportVersion)
            .where(PassportVersion.passport_id == passport_id)
            .order_by(PassportVersion.version_number.desc())
        )
        return list(result.scalars().all())
