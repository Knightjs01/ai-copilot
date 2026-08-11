from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth import security
from app.modules.candidate_auth.models import CandidateUser
from app.modules.phantom_passport.exceptions import CvParsingFailedError, PassportNotFoundError
from app.modules.phantom_passport.llm_client import LLMClient, LLMRequestError
from app.modules.phantom_passport.models import PassportCareerEntry, PhantomPassport
from app.modules.phantom_passport.repository import (
    PassportCareerEntryRepository,
    PassportPersonalInfoRepository,
    PhantomPassportRepository,
)
from app.modules.phantom_passport.schemas import (
    CareerEntryRead,
    CvParseCareerEntry,
    CvParseResult,
    PassportRead,
    PassportUpdate,
    PersonalInfoRead,
)
from app.modules.privacy_gateway.extraction import extract_text
from app.modules.privacy_gateway.redaction import PHONE_PATTERN, redact_text

# Each present field is worth an equal share of 100%, rounded down — simple and legible ("you're
# missing N things") beats a weighted formula nobody can predict.
_COMPLETION_FIELD_COUNT = 10


class PhantomPassportService:
    def __init__(self, session: AsyncSession, llm_client: LLMClient | None = None) -> None:
        self._passports = PhantomPassportRepository(session)
        self._personal_info = PassportPersonalInfoRepository(session)
        self._career_entries = PassportCareerEntryRepository(session)
        self._llm_client = llm_client

    async def get_passport(self, *, candidate: CandidateUser) -> PassportRead:
        passport = await self._passports.get_by_candidate_user_id(candidate.id)
        if passport is None:
            raise PassportNotFoundError()
        return await self._to_read_model(passport)

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
        )

        await self._personal_info.upsert(
            passport_id=passport.id,
            legal_name_encrypted=security.encrypt_secret(body.personal_info.legal_name),
            phone_encrypted=(
                security.encrypt_secret(body.personal_info.phone)
                if body.personal_info.phone
                else None
            ),
            address_encrypted=(
                security.encrypt_secret(body.personal_info.address)
                if body.personal_info.address
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
        self, *, candidate: CandidateUser, content: bytes, content_type: str
    ) -> CvParseResult:
        if self._llm_client is None:
            raise ValueError("parse_cv requires an llm_client")

        # The raw CV is never persisted anywhere — extracted in memory, redacted, sent to the
        # LLM, then discarded. Same zero-retention principle as
        # privacy_gateway.service.sanitize_candidate, applied one step earlier: there's no file
        # upload/storage step here at all, just text extraction from the request body. Reuses
        # the exact same extraction/redaction primitives the company-side candidate flow uses —
        # one redaction implementation for the whole platform, not two.
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
            completion_percentage=_completion_percentage(passport, career_entries),
            personal_info=PersonalInfoRead(
                legal_name=security.decrypt_secret(personal_info.legal_name_encrypted),
                phone=(
                    security.decrypt_secret(personal_info.phone_encrypted)
                    if personal_info.phone_encrypted
                    else None
                ),
                address=(
                    security.decrypt_secret(personal_info.address_encrypted)
                    if personal_info.address_encrypted
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
