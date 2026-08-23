import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.applicant_notes.exceptions import ApplicationNotFoundError
from app.modules.applicant_notes.repository import ApplicantNoteRepository
from app.modules.applicant_notes.schemas import ApplicantNoteRead
from app.modules.auth.models import User
from app.modules.auth.repository.users import UserRepository
from app.modules.shadow_jobs.models import ShadowApplication
from app.modules.shadow_jobs.repository import ShadowApplicationRepository, ShadowJobRepository


class ApplicantNoteService:
    def __init__(self, session: AsyncSession) -> None:
        self._notes = ApplicantNoteRepository(session)
        self._applications = ShadowApplicationRepository(session)
        self._jobs = ShadowJobRepository(session)
        self._users = UserRepository(session)

    async def add_note(
        self, *, actor: User, job_id: uuid.UUID, application_id: uuid.UUID, body: str
    ) -> ApplicantNoteRead:
        application = await self._get_company_application(
            company_id=actor.company_id, job_id=job_id, application_id=application_id
        )
        note = await self._notes.create(
            shadow_application_id=application.id,
            company_id=actor.company_id,
            author_user_id=actor.id,
            body=body,
        )
        return ApplicantNoteRead(
            id=note.id,
            author_user_id=note.author_user_id,
            author_email=actor.email,
            body=note.body,
            created_at=note.created_at,
        )

    async def list_notes(
        self, *, actor: User, job_id: uuid.UUID, application_id: uuid.UUID
    ) -> list[ApplicantNoteRead]:
        application = await self._get_company_application(
            company_id=actor.company_id, job_id=job_id, application_id=application_id
        )
        notes = await self._notes.list_by_application_id(application.id)

        # A handful of notes per applicant in practice -- per-author lookup, not worth a new
        # bulk method on the shared UserRepository for this one small list.
        authors: dict[uuid.UUID, str] = {}
        for author_id in {n.author_user_id for n in notes}:
            author = await self._users.get_by_id(author_id)
            authors[author_id] = author.email if author is not None else "Unknown"

        return [
            ApplicantNoteRead(
                id=n.id,
                author_user_id=n.author_user_id,
                author_email=authors.get(n.author_user_id, "Unknown"),
                body=n.body,
                created_at=n.created_at,
            )
            for n in notes
        ]

    async def _get_company_application(
        self, *, company_id: uuid.UUID, job_id: uuid.UUID, application_id: uuid.UUID
    ) -> ShadowApplication:
        job = await self._jobs.get_by_id(job_id)
        if job is None or job.company_id != company_id or job.deleted_at is not None:
            raise ApplicationNotFoundError()
        application = await self._applications.get_by_id(application_id)
        if application is None or application.shadow_job_id != job_id:
            raise ApplicationNotFoundError()
        return application
