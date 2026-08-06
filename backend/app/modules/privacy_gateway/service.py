import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import AuditService
from app.modules.auth.models import User
from app.modules.candidates.service import CandidateService
from app.modules.candidates.storage import FileStorage
from app.modules.identity_vault.service import IdentityVaultService
from app.modules.privacy_gateway.exceptions import SanitizedProfileNotFoundError
from app.modules.privacy_gateway.extraction import extract_text
from app.modules.privacy_gateway.models import SanitizedProfile
from app.modules.privacy_gateway.redaction import (
    EMAIL_PATTERN,
    LINKEDIN_PATTERN,
    PHONE_PATTERN,
    redact_text,
)
from app.modules.privacy_gateway.repository import SanitizedProfileRepository

_CONTENT_TYPE_TO_LABEL = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}


class PrivacyGatewayService:
    def __init__(self, session: AsyncSession, storage: FileStorage | None = None) -> None:
        self._repository = SanitizedProfileRepository(session)
        # Threading storage through matters: without it, CandidateService would default to its
        # own LocalFileStorage pointed at the real storage_dir, bypassing whatever override the
        # caller (e.g. tests, via get_file_storage) injected — this was a real bug caught by the
        # integration tests (they hit the real /app/storage instead of the per-test tmp_path).
        self._candidates = CandidateService(session, storage=storage)
        self._vault = IdentityVaultService(session)
        self._audit = AuditService(session)

    async def sanitize_candidate(self, *, actor: User, candidate_id: uuid.UUID) -> SanitizedProfile:
        candidate = await self._candidates.get_candidate(
            company_id=actor.company_id, candidate_id=candidate_id
        )
        # download_resume raises ResumeNotFoundError if none is uploaded — the right response
        # either way (nothing to sanitize).
        content, _filename, content_type = await self._candidates.download_resume(
            company_id=actor.company_id, candidate_id=candidate_id
        )

        text = extract_text(content=content, content_type=content_type)

        # Extraction happens on the RAW text, before redact_text() below destroys the matches —
        # best-effort fill of the Identity Vault's email/phone/linkedin_url fields. Only fills
        # fields still NULL; never overwrites a value an Owner already entered manually.
        email_match = EMAIL_PATTERN.search(text)
        phone_match = PHONE_PATTERN.search(text)
        linkedin_match = LINKEDIN_PATTERN.search(text)
        await self._vault.populate_from_sanitize(
            candidate_id=candidate_id,
            email=email_match.group(0) if email_match else None,
            phone=phone_match.group(0) if phone_match else None,
            linkedin_url=linkedin_match.group(0) if linkedin_match else None,
        )

        known_full_name = await self._vault.get_decrypted_full_name(candidate_id)
        redacted_text, counts = redact_text(text=text, known_full_name=known_full_name)

        profile = await self._repository.upsert(
            company_id=actor.company_id,
            candidate_id=candidate_id,
            redacted_text=redacted_text,
            redaction_counts=counts,
            source_file_type=_CONTENT_TYPE_TO_LABEL.get(content_type, "unknown"),
            processed_at=datetime.now(timezone.utc),
        )

        # The original CV must not persist on the platform once processed (CLAUDE.md).
        await self._candidates.clear_resume(actor=actor, candidate_id=candidate_id)

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="candidate.sanitized",
            target_type="candidate",
            target_id=candidate.id,
            extra_data=counts,
        )
        return profile

    async def get_sanitized_profile(
        self, *, company_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> SanitizedProfile:
        profile = await self._repository.get_by_candidate_id(candidate_id)
        if profile is None or profile.company_id != company_id or profile.deleted_at is not None:
            raise SanitizedProfileNotFoundError()
        return profile
