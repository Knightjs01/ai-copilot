import secrets
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.auth import security
from app.modules.candidate_auth.models import CandidateUser
from app.modules.candidates.storage import EncryptingFileStorage, FileStorage, LocalFileStorage
from app.modules.phantom_passport.exceptions import (
    AiSuggestionFailedError,
    CallsignGenerationExhaustedError,
    CvParsingFailedError,
    InvalidCvFileError,
    OriginalCvNotFoundError,
    PassportNotFoundError,
)
from app.modules.phantom_passport.llm_client import LLMClient, LLMRequestError
from app.modules.phantom_passport.models import PassportCareerEntry, PhantomPassport
from app.modules.phantom_passport.repository import (
    CandidateCvDocumentRepository,
    PassportCareerEntryRepository,
    PassportPersonalInfoRepository,
    PassportVersionRepository,
    PhantomPassportRepository,
)
from app.modules.phantom_passport.schemas import (
    CareerEntryRead,
    CvDocumentRead,
    CvParseCareerEntry,
    CvParseResult,
    IndustriesSuggestionResponse,
    PassportRead,
    PassportUpdate,
    PassportVerificationRead,
    PassportVersionRead,
    PersonalInfoRead,
    ShadowProfileSnapshot,
    SkillsSuggestionResponse,
    SummaryImprovementResponse,
)
from app.modules.privacy_gateway.extraction import extract_text
from app.modules.privacy_gateway.redaction import PHONE_PATTERN, redact_text

# Each present field is worth an equal share of 100%, rounded down — simple and legible ("you're
# missing N things") beats a weighted formula nobody can predict.
_COMPLETION_FIELD_COUNT = 10

# Same set as app.modules.candidates.service — a CV is a CV — but kept as a local module-level
# constant rather than imported, since that one is private to the candidates module.
_ALLOWED_CV_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}

# A third, deliberately independent word pool — shadow_jobs.service already establishes the
# convention that Shadow (per-application) and ATS (per-project) Callsigns use separate pools by
# design, so two independent identity systems never visually collide. A Passport-level Callsign
# is a third, similarly independent concept: one stable identity for the Passport itself, never
# regenerated, and never exposed on any company-facing schema (see PassportRead's own comment).
_PASSPORT_CALLSIGN_WORDS = [
    "Nova", "Pulse", "Vertex", "Aurora", "Zephyr", "Meridian", "Solstice", "Tundra",
    "Cascade", "Harbor", "Prism", "Kestrel", "Obsidian", "Willow", "Beacon", "Compass",
]  # fmt: skip
_MAX_CALLSIGN_ATTEMPTS = 5


class PhantomPassportService:
    def __init__(
        self,
        session: AsyncSession,
        llm_client: LLMClient | None = None,
        storage: FileStorage | None = None,
    ) -> None:
        self._settings = get_settings()
        self._session = session
        self._passports = PhantomPassportRepository(session)
        self._personal_info = PassportPersonalInfoRepository(session)
        self._career_entries = PassportCareerEntryRepository(session)
        self._cv_documents = CandidateCvDocumentRepository(session)
        self._versions = PassportVersionRepository(session)
        self._llm_client = llm_client
        self._storage = storage or EncryptingFileStorage(LocalFileStorage())

    async def get_passport(self, *, candidate: CandidateUser) -> PassportRead:
        passport = await self._passports.get_by_candidate_user_id(candidate.id)
        if passport is None:
            raise PassportNotFoundError()
        return await self._to_read_model(passport)

    async def get_verification_by_callsign(self, callsign: str) -> PassportVerificationRead | None:
        """Public verification lookup -- a callsign only ever exists post-approval (see
        approve_passport), so there's no separate "not approved" branch to handle here."""
        passport = await self._passports.get_by_callsign(callsign)
        if passport is None or passport.callsign is None:
            return None
        career_entries = await self._career_entries.list_by_passport_id(passport.id)
        return PassportVerificationRead(
            callsign=passport.callsign,
            headline=passport.headline,
            seniority=passport.seniority,
            verification_status=passport.verification_status,
            completion_percentage=_completion_percentage(passport, career_entries),
        )

    async def save_passport(
        self, *, candidate: CandidateUser, body: PassportUpdate
    ) -> PassportRead:
        passport = await self._passports.upsert(
            candidate_user_id=candidate.id,
            headline=body.headline,
            seniority=body.seniority,
            years_experience=body.years_experience,
            summary=body.summary,
            skills=body.skills,
            industries=body.industries,
            location=body.location,
            remote_preference=body.remote_preference,
            salary_min=body.salary_min,
            salary_max=body.salary_max,
            notice_period=body.notice_period,
            career_intent=body.career_intent or "just_exploring",
            visibility=body.visibility or "private",
        )

        await self._personal_info.upsert(
            passport_id=passport.id,
            legal_name_encrypted=security.encrypt_secret(body.personal_info.legal_name),
            phone_encrypted=(
                security.encrypt_secret(body.personal_info.phone)
                if body.personal_info.phone
                else None
            ),
        )

        await self._career_entries.replace_all(
            passport_id=passport.id,
            entries=[
                {
                    "title": entry.title,
                    "company_name_encrypted": security.encrypt_secret(entry.company_name),
                    "company_name_anonymized": entry.company_name_anonymized,
                    "start_date": entry.start_date,
                    "end_date": entry.end_date,
                    "is_current": entry.is_current,
                    "responsibilities": entry.responsibilities,
                    "achievements": entry.achievements,
                }
                for entry in body.career_entries
            ],
        )

        return await self._to_read_model(passport)

    async def parse_cv(
        self,
        *,
        candidate: CandidateUser,
        content: bytes,
        content_type: str,
        original_filename: str,
    ) -> CvParseResult:
        if self._llm_client is None:
            raise ValueError("parse_cv requires an llm_client")

        extension = _ALLOWED_CV_CONTENT_TYPES.get(content_type)
        if extension is None:
            raise InvalidCvFileError("CV must be a PDF, DOC, or DOCX file — got: " + content_type)
        max_bytes = self._settings.max_resume_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise InvalidCvFileError(f"CV exceeds the {self._settings.max_resume_size_mb}MB limit")

        # The original file is now stored in the candidate's private Vault — reverses this
        # module's original zero-file-retention design (extracted, redacted, discarded) per the
        # Candidate Vault requirement: upload no longer means "gone forever after parsing," it
        # means "kept private and never recruiter-visible." Persisted before extraction so a
        # parse failure below still leaves the candidate's original safely stored. Replaces any
        # prior document (delete old key), matching candidates/service.py::upload_resume.
        existing_document = await self._cv_documents.get_by_candidate_user_id(candidate.id)
        old_storage_key = existing_document.storage_key if existing_document else None
        storage_key = f"candidate-cv/{candidate.id}/{uuid.uuid4()}{extension}"
        await self._storage.save(key=storage_key, content=content, content_type=content_type)
        await self._cv_documents.upsert(
            candidate_user_id=candidate.id,
            storage_key=storage_key,
            original_filename=original_filename,
            content_type=content_type,
            file_size=len(content),
        )
        # Committed here, not left to the request-scoped session's end-of-request commit (see
        # app.db.session.get_db) — that dependency rolls back the WHOLE transaction if anything
        # later in this same request raises, and extraction/redaction/the LLM call below can
        # fail independently of whether the Vault write should survive. Without this, a CV that
        # fails to parse would silently orphan the just-written encrypted file on disk with no
        # DB row pointing to it — the opposite of "the original always stays in your Vault."
        # expire_on_commit=False (see app.db.base) means ORM objects fetched below, in this same
        # request, stay perfectly usable after this commit.
        await self._session.commit()
        if old_storage_key is not None:
            await self._storage.delete(key=old_storage_key)

        # Extraction/redaction/LLM proceed exactly as before — the LLM only ever sees redacted
        # text, never the stored original file. Reuses the exact same extraction/redaction
        # primitives the company-side candidate flow uses — one redaction implementation for the
        # whole platform, not two.
        text = extract_text(content=content, content_type=content_type)

        # Email isn't extracted here — the candidate's email is already known from
        # candidate_auth signup, so there's nothing new for a CV-parse preview to surface.
        phone_match = PHONE_PATTERN.search(text)

        redacted_text, _counts = redact_text(text=text, known_full_name=candidate.full_name)

        try:
            extraction = await self._llm_client.extract_passport_from_cv(
                redacted_text=redacted_text
            )
        except LLMRequestError as exc:
            raise CvParsingFailedError(str(exc)) from exc

        return CvParseResult(
            headline=extraction.headline or None,
            seniority=extraction.seniority or None,
            years_experience=extraction.years_experience,
            summary=extraction.summary or None,
            skills=extraction.skills,
            industries=extraction.industries,
            career_entries=[
                CvParseCareerEntry(
                    title=entry.title,
                    company_name=entry.company_name,
                    company_name_anonymized=entry.company_name_anonymized,
                    start_date=entry.start_date,
                    end_date=entry.end_date,
                    is_current=entry.is_current,
                    responsibilities=entry.responsibilities or None,
                    achievements=entry.achievements,
                )
                for entry in extraction.career_entries
            ],
            detected_phone=phone_match.group(0) if phone_match else None,
            # Street-address extraction isn't exposed as a public pattern from
            # privacy_gateway.redaction (only email/phone/linkedin are) — the candidate enters
            # their address manually in the Passport form instead of it being auto-detected.
            detected_address=None,
        )

    # --- Candidate Vault (original CV custody) ------------------------------------------------

    async def get_original_cv_status(self, *, candidate: CandidateUser) -> CvDocumentRead:
        document = await self._cv_documents.get_by_candidate_user_id(candidate.id)
        if document is None:
            raise OriginalCvNotFoundError()
        return CvDocumentRead(
            original_filename=document.original_filename,
            content_type=document.content_type,
            file_size=document.file_size,
            uploaded_at=document.uploaded_at,
        )

    async def download_original_cv(self, *, candidate: CandidateUser) -> tuple[bytes, str, str]:
        document = await self._cv_documents.get_by_candidate_user_id(candidate.id)
        if document is None:
            raise OriginalCvNotFoundError()
        content = await self._storage.read(key=document.storage_key)
        return content, document.content_type, document.original_filename

    async def delete_original_cv(self, *, candidate: CandidateUser) -> None:
        document = await self._cv_documents.get_by_candidate_user_id(candidate.id)
        if document is None:
            raise OriginalCvNotFoundError()
        await self._storage.delete(key=document.storage_key)
        await self._cv_documents.delete(document)

    # --- Approval gate & versioned snapshots --------------------------------------------------

    async def approve_passport(self, *, candidate: CandidateUser) -> PassportVersionRead:
        passport = await self._passports.get_by_candidate_user_id(candidate.id)
        if passport is None:
            raise PassportNotFoundError()
        personal_info = await self._personal_info.get_by_passport_id(passport.id)
        if personal_info is None:
            raise PassportNotFoundError("Passport is missing its personal information record")

        # Built from a fresh read of live data, inside this same call — career entry rows get
        # hard-deleted-and-reinserted on every PUT /me (see PassportCareerEntryRepository
        # .replace_all), so their primary keys are never stable across saves. The snapshot has to
        # copy field values by value, not reference rows that may not exist by the time anyone
        # reads it back.
        career_entries = await self._career_entries.list_by_passport_id(passport.id)
        snapshot = ShadowProfileSnapshot(
            headline=passport.headline,
            seniority=passport.seniority,
            years_experience=passport.years_experience,
            summary=passport.summary,
            skills=list(passport.skills),
            industries=list(passport.industries),
            location=passport.location,
            remote_preference=passport.remote_preference,
            salary_min=passport.salary_min,
            salary_max=passport.salary_max,
            notice_period=passport.notice_period,
            career_intent=passport.career_intent,
            career_entries=[
                {
                    "title": entry.title,
                    "company_name_anonymized": entry.company_name_anonymized,
                    "is_current": entry.is_current,
                    "start_date": entry.start_date.isoformat() if entry.start_date else None,
                    "end_date": entry.end_date.isoformat() if entry.end_date else None,
                    "responsibilities": entry.responsibilities,
                    "achievements": list(entry.achievements),
                }
                for entry in career_entries
            ],
        )

        cv_document = await self._cv_documents.get_by_candidate_user_id(candidate.id)
        next_version_number = await self._versions.get_latest_version_number(passport.id) + 1
        version = await self._versions.create(
            passport_id=passport.id,
            version_number=next_version_number,
            snapshot=snapshot.model_dump(mode="json"),
            source_cv_document_id=cv_document.id if cv_document else None,
            source_cv_filename=cv_document.original_filename if cv_document else None,
        )
        await self._passports.set_current_version(passport, version_id=version.id)

        # Generated once, at first approval only — never regenerated on later re-approvals.
        if passport.callsign is None:
            callsign = await self._generate_callsign()
            await self._passports.set_callsign(passport, callsign=callsign)

        return PassportVersionRead(
            id=version.id,
            version_number=version.version_number,
            approved_at=version.approved_at,
            source_cv_filename=version.source_cv_filename,
        )

    async def _generate_callsign(self) -> str:
        for _ in range(_MAX_CALLSIGN_ATTEMPTS):
            callsign = f"{secrets.choice(_PASSPORT_CALLSIGN_WORDS)}-{secrets.randbelow(90) + 10}"
            if not await self._passports.callsign_exists(callsign):
                return callsign
        raise CallsignGenerationExhaustedError()

    # --- AI co-pilot (opt-in suggestions, never silently applied) -----------------------------

    async def suggest_summary_improvement(
        self, *, headline: str | None, summary: str, skills: list[str]
    ) -> SummaryImprovementResponse:
        if self._llm_client is None:
            raise ValueError("suggest_summary_improvement requires an llm_client")
        try:
            suggestion = await self._llm_client.suggest_summary_improvement(
                headline=headline, summary=summary, skills=skills
            )
        except LLMRequestError as exc:
            raise AiSuggestionFailedError(str(exc)) from exc
        return SummaryImprovementResponse(suggested_summary=suggestion)

    async def suggest_skills(
        self, *, headline: str | None, summary: str | None, existing_skills: list[str]
    ) -> SkillsSuggestionResponse:
        if self._llm_client is None:
            raise ValueError("suggest_skills requires an llm_client")
        try:
            suggestions = await self._llm_client.suggest_skills(
                headline=headline, summary=summary, existing_skills=existing_skills
            )
        except LLMRequestError as exc:
            raise AiSuggestionFailedError(str(exc)) from exc
        return SkillsSuggestionResponse(suggested_skills=suggestions)

    async def suggest_industries(
        self, *, headline: str | None, summary: str | None, existing_industries: list[str]
    ) -> IndustriesSuggestionResponse:
        if self._llm_client is None:
            raise ValueError("suggest_industries requires an llm_client")
        try:
            suggestions = await self._llm_client.suggest_industries(
                headline=headline, summary=summary, existing_industries=existing_industries
            )
        except LLMRequestError as exc:
            raise AiSuggestionFailedError(str(exc)) from exc
        return IndustriesSuggestionResponse(suggested_industries=suggestions)

    async def list_versions(self, *, candidate: CandidateUser) -> list[PassportVersionRead]:
        # A list endpoint — "no Passport yet" is just zero versions, not an error, matching
        # every other list-of-a-candidate's-own-things endpoint in this app.
        passport = await self._passports.get_by_candidate_user_id(candidate.id)
        if passport is None:
            return []
        versions = await self._versions.list_by_passport_id(passport.id)
        return [
            PassportVersionRead(
                id=v.id,
                version_number=v.version_number,
                approved_at=v.approved_at,
                source_cv_filename=v.source_cv_filename,
            )
            for v in versions
        ]

    async def _to_read_model(self, passport: PhantomPassport) -> PassportRead:
        personal_info = await self._personal_info.get_by_passport_id(passport.id)
        if personal_info is None:
            # save_passport always writes PhantomPassport and PassportPersonalInfo together —
            # reaching this means a passport row exists without its personal info, which is a
            # data integrity bug, not a valid state to paper over silently.
            raise PassportNotFoundError("Passport is missing its personal information record")

        career_entries: list[PassportCareerEntry] = await self._career_entries.list_by_passport_id(
            passport.id
        )

        current_version_number = None
        if passport.current_version_id is not None:
            current_version = await self._versions.get_by_id(passport.current_version_id)
            current_version_number = current_version.version_number if current_version else None

        return PassportRead(
            id=passport.id,
            headline=passport.headline,
            seniority=passport.seniority,
            years_experience=passport.years_experience,
            summary=passport.summary,
            skills=list(passport.skills),
            industries=list(passport.industries),
            location=passport.location,
            remote_preference=passport.remote_preference,
            salary_min=passport.salary_min,
            salary_max=passport.salary_max,
            notice_period=passport.notice_period,
            career_intent=passport.career_intent,
            verification_status=passport.verification_status,
            visibility=passport.visibility,
            completion_percentage=_completion_percentage(passport, career_entries),
            current_version_number=current_version_number,
            callsign=passport.callsign,
            personal_info=PersonalInfoRead(
                legal_name=security.decrypt_secret(personal_info.legal_name_encrypted),
                phone=(
                    security.decrypt_secret(personal_info.phone_encrypted)
                    if personal_info.phone_encrypted
                    else None
                ),
            ),
            career_entries=[
                CareerEntryRead(
                    id=entry.id,
                    title=entry.title,
                    company_name=security.decrypt_secret(entry.company_name_encrypted),
                    company_name_anonymized=entry.company_name_anonymized,
                    start_date=entry.start_date,
                    end_date=entry.end_date,
                    is_current=entry.is_current,
                    responsibilities=entry.responsibilities,
                    achievements=list(entry.achievements),
                )
                for entry in career_entries
            ],
        )


def _completion_percentage(
    passport: PhantomPassport, career_entries: list[PassportCareerEntry]
) -> int:
    filled = 0
    if passport.headline:
        filled += 1
    if passport.summary:
        filled += 1
    if passport.skills:
        filled += 1
    if passport.industries:
        filled += 1
    if passport.location:
        filled += 1
    if passport.remote_preference:
        filled += 1
    if passport.salary_min and passport.salary_max:
        filled += 1
    if passport.notice_period:
        filled += 1
    if career_entries:
        filled += 1
    if any(entry.achievements for entry in career_entries):
        filled += 1
    return round(filled / _COMPLETION_FIELD_COUNT * 100)
