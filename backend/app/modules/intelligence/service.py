import uuid
from dataclasses import asdict
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.audit.service import AuditService
from app.modules.auth.models import User
from app.modules.intelligence.exceptions import (
    IntelligencePackGenerationError,
    IntelligencePackNotFoundError,
)
from app.modules.intelligence.llm_client import LLMClient, LLMRequestError
from app.modules.intelligence.models import IntelligencePack
from app.modules.intelligence.repository import IntelligencePackRepository
from app.modules.privacy_gateway.service import PrivacyGatewayService


class IntelligenceService:
    def __init__(self, session: AsyncSession, llm_client: LLMClient | None = None) -> None:
        # llm_client is only needed by generate_pack — get_pack (a pure read) doesn't touch the
        # LLM at all, so routes that only read shouldn't need to inject/construct one.
        self._settings = get_settings()
        self._repository = IntelligencePackRepository(session)
        self._privacy_gateway = PrivacyGatewayService(session)
        self._audit = AuditService(session)
        self._llm_client = llm_client

    async def generate_pack(self, *, actor: User, candidate_id: uuid.UUID) -> IntelligencePack:
        if self._llm_client is None:
            raise ValueError("generate_pack requires an llm_client")

        # Raises SanitizedProfileNotFoundError (404) if this candidate hasn't been through the
        # Phase 4 Privacy Gateway yet — that's the enforcement point for "never send raw CV data
        # to an LLM": there is no code path here that can reach anything but redacted_text.
        profile = await self._privacy_gateway.get_sanitized_profile(
            company_id=actor.company_id, candidate_id=candidate_id
        )

        try:
            extraction = await self._llm_client.extract_candidate_profile(
                redacted_text=profile.redacted_text
            )
        except LLMRequestError as exc:
            raise IntelligencePackGenerationError(str(exc)) from exc

        pack = await self._repository.upsert(
            company_id=actor.company_id,
            candidate_id=candidate_id,
            skills=extraction.skills,
            experience_summary=extraction.experience_summary,
            education=[asdict(entry) for entry in extraction.education],
            narrative_summary=extraction.narrative_summary,
            model_used=self._settings.anthropic_model,
            generated_at=datetime.now(timezone.utc),
        )

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="candidate.intelligence_pack_generated",
            target_type="candidate",
            target_id=candidate_id,
            extra_data={"model": self._settings.anthropic_model},
        )
        return pack

    async def get_pack(self, *, company_id: uuid.UUID, candidate_id: uuid.UUID) -> IntelligencePack:
        pack = await self._repository.get_by_candidate_id(candidate_id)
        if pack is None or pack.company_id != company_id or pack.deleted_at is not None:
            raise IntelligencePackNotFoundError()
        return pack
