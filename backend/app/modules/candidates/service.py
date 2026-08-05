import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.audit.service import AuditService
from app.modules.auth.models import User
from app.modules.candidates.exceptions import (
    CandidateNotFoundError,
    InvalidResumeFileError,
    ResumeNotFoundError,
)
from app.modules.candidates.models import (
    Candidate,
    CandidateSource,
    CandidateStatus,
    PrescreenOutcome,
)
from app.modules.candidates.repository import CandidateRepository
from app.modules.candidates.storage import FileStorage, LocalFileStorage
from app.modules.projects.service import ProjectService

_ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}
_EXTENSION_TO_CONTENT_TYPE = {
    ext: content_type for content_type, ext in _ALLOWED_CONTENT_TYPES.items()
}


class CandidateService:
    def __init__(self, session: AsyncSession, storage: FileStorage | None = None) -> None:
        self._settings = get_settings()
        self._repository = CandidateRepository(session)
        self._projects = ProjectService(session)
        self._audit = AuditService(session)
        self._storage = storage or LocalFileStorage()

    async def create_candidate(
        self,
        *,
        actor: User,
        project_id: uuid.UUID,
        full_name: str,
        email: str | None,
        phone: str | None,
        source: CandidateSource,
        status: CandidateStatus,
    ) -> Candidate:
        # Confirms project_id belongs to the actor's company — going through the service layer
        # (not ProjectRepository directly) per the module contract; raises ProjectNotFoundError
        # (a 404) if it's missing or belongs to another company, which is the correct response
        # either way from the caller's point of view.
        await self._projects.get_project(company_id=actor.company_id, project_id=project_id)

        candidate = await self._repository.create(
            company_id=actor.company_id,
            project_id=project_id,
            full_name=full_name,
            email=email,
            phone=phone,
            source=source,
            status=status,
            created_by_id=actor.id,
        )
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="candidate.created",
            target_type="candidate",
            target_id=candidate.id,
        )
        return candidate

    async def get_candidate(self, *, company_id: uuid.UUID, candidate_id: uuid.UUID) -> Candidate:
        candidate = await self._repository.get_by_id(candidate_id)
        if (
            candidate is None
            or candidate.company_id != company_id
            or candidate.deleted_at is not None
        ):
            raise CandidateNotFoundError()
        return candidate

    async def list_candidates(
        self,
        *,
        company_id: uuid.UUID,
        project_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Candidate]:
        return await self._repository.list_by_company(
            company_id, project_id=project_id, limit=limit, offset=offset
        )

    async def update_candidate(
        self,
        *,
        actor: User,
        candidate_id: uuid.UUID,
        full_name: str | None,
        email: str | None,
        phone: str | None,
        source: CandidateSource | None,
        status: CandidateStatus | None,
        interview_scheduled_at: datetime | None = None,
        prescreen_outcome: PrescreenOutcome | None = None,
        prescreen_notes: str | None = None,
    ) -> Candidate:
        candidate = await self.get_candidate(company_id=actor.company_id, candidate_id=candidate_id)

        if full_name is not None:
            candidate.full_name = full_name
        if email is not None:
            candidate.email = email
        if phone is not None:
            candidate.phone = phone
        if source is not None:
            candidate.source = source.value
        if status is not None:
            candidate.status = status.value
        if interview_scheduled_at is not None:
            candidate.interview_scheduled_at = interview_scheduled_at
        if prescreen_outcome is not None:
            candidate.prescreen_outcome = prescreen_outcome.value
        if prescreen_notes is not None:
            candidate.prescreen_notes = prescreen_notes

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="candidate.updated",
            target_type="candidate",
            target_id=candidate.id,
        )
        return candidate

    async def delete_candidate(self, *, actor: User, candidate_id: uuid.UUID) -> None:
        candidate = await self.get_candidate(company_id=actor.company_id, candidate_id=candidate_id)
        candidate.deleted_at = datetime.now(timezone.utc)

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="candidate.deleted",
            target_type="candidate",
            target_id=candidate.id,
        )

    async def upload_resume(
        self,
        *,
        actor: User,
        candidate_id: uuid.UUID,
        content: bytes,
        content_type: str,
        original_filename: str,
    ) -> Candidate:
        extension = _ALLOWED_CONTENT_TYPES.get(content_type)
        if extension is None:
            raise InvalidResumeFileError(
                "Resume must be a PDF, DOC, or DOCX file — got: " + content_type
            )
        max_bytes = self._settings.max_resume_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise InvalidResumeFileError(
                f"Resume exceeds the {self._settings.max_resume_size_mb}MB limit"
            )

        candidate = await self.get_candidate(company_id=actor.company_id, candidate_id=candidate_id)

        key = f"{actor.company_id}/{candidate.id}/{uuid.uuid4()}{extension}"
        await self._storage.save(key=key, content=content, content_type=content_type)

        old_key = candidate.resume_file_key
        candidate.resume_file_key = key
        candidate.resume_original_filename = original_filename
        if old_key is not None:
            await self._storage.delete(key=old_key)

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="candidate.resume_uploaded",
            target_type="candidate",
            target_id=candidate.id,
        )
        return candidate

    async def download_resume(
        self, *, company_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> tuple[bytes, str, str]:
        """Returns (content, original_filename, content_type). content_type is inferred from the
        stored key's extension — we don't persist it separately since it's fully determined by
        the extension already recorded at upload time."""

        candidate = await self.get_candidate(company_id=company_id, candidate_id=candidate_id)
        if candidate.resume_file_key is None:
            raise ResumeNotFoundError()

        content = await self._storage.read(key=candidate.resume_file_key)
        filename = candidate.resume_original_filename or "resume"
        extension = "." + candidate.resume_file_key.rsplit(".", 1)[-1]
        content_type = _EXTENSION_TO_CONTENT_TYPE.get(extension, "application/octet-stream")
        return content, filename, content_type

    async def clear_resume(self, *, actor: User, candidate_id: uuid.UUID) -> Candidate:
        """Deletes the stored resume file and clears its reference from the candidate record —
        used by the privacy_gateway module once a resume has been sanitized, per CLAUDE.md's
        rule that the original CV upload must not persist on the platform after processing."""

        candidate = await self.get_candidate(company_id=actor.company_id, candidate_id=candidate_id)
        if candidate.resume_file_key is None:
            raise ResumeNotFoundError()

        await self._storage.delete(key=candidate.resume_file_key)
        candidate.resume_file_key = None
        candidate.resume_original_filename = None

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="candidate.resume_cleared",
            target_type="candidate",
            target_id=candidate.id,
        )
        return candidate
