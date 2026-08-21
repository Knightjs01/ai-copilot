import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.audit.service import AuditService
from app.modules.auth.models import User
from app.modules.candidates.service import CandidateService
from app.modules.hiring_blueprint.exceptions import HiringBlueprintNotFoundError
from app.modules.hiring_blueprint.service import HiringBlueprintService
from app.modules.hiring_manager_alignment.exceptions import HiringManagerAlignmentNotFoundError
from app.modules.hiring_manager_alignment.service import HiringManagerAlignmentService
from app.modules.identity_vault.service import IdentityVaultService
from app.modules.intelligence.service import IntelligenceService
from app.modules.prescreen_assessment.exceptions import (
    MissingHiringBlueprintError,
    MissingHiringManagerAlignmentError,
    PrescreenAssessmentGenerationError,
    PrescreenAssessmentNotFoundError,
    PrescreenNotesRequiredError,
)
from app.modules.prescreen_assessment.llm_client import (
    LLMRequestError,
    PrescreenAssessmentLLMClient,
)
from app.modules.prescreen_assessment.models import PrescreenAssessment
from app.modules.prescreen_assessment.repository import PrescreenAssessmentRepository
from app.modules.privacy_gateway.redaction import redact_text


class PrescreenAssessmentService:
    def __init__(
        self, session: AsyncSession, llm_client: PrescreenAssessmentLLMClient | None = None
    ) -> None:
        # llm_client is only needed by the two generate_* methods — get_assessment (a pure
        # read) doesn't touch the LLM at all, so routes that only read shouldn't need to
        # inject/construct one.
        self._settings = get_settings()
        self._repository = PrescreenAssessmentRepository(session)
        self._candidates = CandidateService(session)
        self._intelligence = IntelligenceService(session)
        self._blueprints = HiringBlueprintService(session)
        self._alignments = HiringManagerAlignmentService(session)
        self._vault = IdentityVaultService(session)
        self._audit = AuditService(session)
        self._llm_client = llm_client

    async def generate_assessment(
        self, *, actor: User, candidate_id: uuid.UUID
    ) -> PrescreenAssessment:
        if self._llm_client is None:
            raise ValueError("generate_assessment requires an llm_client")

        candidate = await self._candidates.get_candidate(
            company_id=actor.company_id, candidate_id=candidate_id
        )

        # Raises IntelligencePackNotFoundError (404, existing) if this candidate hasn't been
        # through Phase 5 yet — same enforcement pattern as every prerequisite in this codebase.
        pack = await self._intelligence.get_pack(
            company_id=actor.company_id, candidate_id=candidate_id
        )

        try:
            blueprint = await self._blueprints.get_blueprint(
                company_id=actor.company_id, project_id=candidate.project_id
            )
        except HiringBlueprintNotFoundError as exc:
            raise MissingHiringBlueprintError() from exc

        try:
            alignment = await self._alignments.get_alignment(
                company_id=actor.company_id, project_id=candidate.project_id
            )
        except HiringManagerAlignmentNotFoundError as exc:
            raise MissingHiringManagerAlignmentError() from exc

        try:
            extraction = await self._llm_client.generate_assessment(
                role_summary=blueprint.role_summary,
                must_have_qualifications=blueprint.must_have_qualifications,
                nice_to_have_qualifications=blueprint.nice_to_have_qualifications,
                key_responsibilities=blueprint.key_responsibilities,
                evaluation_criteria=blueprint.evaluation_criteria,
                top_requirements=alignment.top_requirements,
                candidate_skills=pack.skills,
                candidate_experience_summary=pack.experience_summary,
                candidate_education=pack.education,
                candidate_industry=pack.industry,
                candidate_years_experience=pack.years_experience,
            )
        except LLMRequestError as exc:
            raise PrescreenAssessmentGenerationError(str(exc)) from exc

        assessment = await self._repository.upsert_assessment(
            company_id=actor.company_id,
            candidate_id=candidate_id,
            fit_rating=extraction.fit_rating,
            fit_summary=extraction.fit_summary,
            strengths=extraction.strengths,
            gaps=extraction.gaps,
            suggested_questions=extraction.suggested_questions,
            areas_to_probe=extraction.areas_to_probe,
            model_used=self._settings.anthropic_model,
            generated_at=datetime.now(timezone.utc),
        )

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="candidate.prescreen_assessment_generated",
            target_type="candidate",
            target_id=candidate_id,
            extra_data={"model": self._settings.anthropic_model},
        )
        return assessment

    async def generate_handoff_recommendations(
        self, *, actor: User, candidate_id: uuid.UUID
    ) -> PrescreenAssessment:
        if self._llm_client is None:
            raise ValueError("generate_handoff_recommendations requires an llm_client")

        candidate = await self._candidates.get_candidate(
            company_id=actor.company_id, candidate_id=candidate_id
        )
        if not candidate.prescreen_notes:
            raise PrescreenNotesRequiredError()

        assessment = await self.get_assessment(
            company_id=actor.company_id, candidate_id=candidate_id
        )

        # prescreen_notes is recruiter free text and bypasses the privacy gateway entirely — it's
        # the one place a real name could otherwise leak into an LLM prompt, so it gets the same
        # name-redaction pass here, using the vault's decrypted name as the known name to strip.
        known_full_name = await self._vault.get_decrypted_full_name(candidate_id)
        redacted_notes, _ = redact_text(
            text=candidate.prescreen_notes, known_full_name=known_full_name
        )

        try:
            recommendations = await self._llm_client.generate_handoff_recommendations(
                fit_summary=assessment.fit_summary,
                gaps=assessment.gaps,
                areas_to_probe=assessment.areas_to_probe,
                prescreen_notes=redacted_notes,
            )
        except LLMRequestError as exc:
            raise PrescreenAssessmentGenerationError(str(exc)) from exc

        updated = await self._repository.set_handoff_recommendations(
            assessment=assessment, handoff_recommendations=recommendations
        )

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="candidate.handoff_recommendations_generated",
            target_type="candidate",
            target_id=candidate_id,
            extra_data={"model": self._settings.anthropic_model},
        )
        return updated

    async def get_assessment(
        self, *, company_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> PrescreenAssessment:
        assessment = await self._repository.get_by_candidate_id(candidate_id)
        if (
            assessment is None
            or assessment.company_id != company_id
            or assessment.deleted_at is not None
        ):
            raise PrescreenAssessmentNotFoundError()
        return assessment
