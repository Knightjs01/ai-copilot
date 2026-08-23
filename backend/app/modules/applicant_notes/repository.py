import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.applicant_notes.models import ApplicantNote


class ApplicantNoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        shadow_application_id: uuid.UUID,
        company_id: uuid.UUID,
        author_user_id: uuid.UUID,
        body: str,
    ) -> ApplicantNote:
        note = ApplicantNote(
            shadow_application_id=shadow_application_id,
            company_id=company_id,
            author_user_id=author_user_id,
            body=body,
        )
        self._session.add(note)
        await self._session.flush()
        return note

    async def list_by_application_id(self, shadow_application_id: uuid.UUID) -> list[ApplicantNote]:
        result = await self._session.execute(
            select(ApplicantNote)
            .where(ApplicantNote.shadow_application_id == shadow_application_id)
            .order_by(ApplicantNote.created_at.desc())
        )
        return list(result.scalars().all())
