import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.privacy_gateway.models import SanitizedProfile


class SanitizedProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_candidate_id(self, candidate_id: uuid.UUID) -> SanitizedProfile | None:
        result = await self._session.execute(
            select(SanitizedProfile).where(SanitizedProfile.candidate_id == candidate_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        company_id: uuid.UUID,
        candidate_id: uuid.UUID,
        redacted_text: str,
        redaction_counts: dict[str, Any],
        source_file_type: str,
        processed_at: datetime,
    ) -> SanitizedProfile:
        existing = await self.get_by_candidate_id(candidate_id)
        if existing is not None:
            existing.redacted_text = redacted_text
            existing.redaction_counts = redaction_counts
            existing.source_file_type = source_file_type
            existing.processed_at = processed_at
            await self._session.flush()
            return existing

        profile = SanitizedProfile(
            company_id=company_id,
            candidate_id=candidate_id,
            redacted_text=redacted_text,
            redaction_counts=redaction_counts,
            source_file_type=source_file_type,
            processed_at=processed_at,
        )
        self._session.add(profile)
        await self._session.flush()
        return profile
