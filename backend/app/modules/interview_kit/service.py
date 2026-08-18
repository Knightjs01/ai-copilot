import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.audit.service import AuditService
from app.modules.auth.models import User
from app.modules.hiring_blueprint.exceptions import HiringBlueprintNotFoundError
from app.modules.hiring_blueprint.service import HiringBlueprintService
from app.modules.interview_kit.exceptions import (
    InterviewKitGenerationError,
    InterviewKitNotFoundError,
    MissingHiringBlueprintError,
)
from app.modules.interview_kit.llm_client import InterviewKitLLMClient, LLMRequestError
from app.modules.interview_kit.models import InterviewKit
from app.modules.interview_kit.repository import InterviewKitRepository


class InterviewKitService:
    def __init__(
        self, session: AsyncSession, llm_client: InterviewKitLLMClient | None = None
    ) -> None:
        # llm_client is only needed by generate_kit — get_kit (a pure read) doesn't touch the
        # LLM at all, so routes that only read shouldn't need to inject/construct one.
        self._settings = get_settings()
        self._repository = InterviewKitRepository(session)
        self._blueprints = HiringBlueprintService(session)
        self._audit = AuditService(session)
        self._llm_client = llm_client

    async def generate_kit(self, *, actor: User, project_id: uuid.UUID) -> InterviewKit:
        if self._llm_client is None:
            raise ValueError("generate_kit requires an llm_client")

        try:
            blueprint = await self._blueprints.get_blueprint(
                company_id=actor.company_id, project_id=project_id
            )
        except HiringBlueprintNotFoundError as exc:
            raise MissingHiringBlueprintError() from exc

        try:
            extraction = await self._llm_client.generate_kit(
                role_summary=blueprint.role_summary,
                must_have_qualifications=blueprint.must_have_qualifications,
                evaluation_criteria=blueprint.evaluation_criteria,
            )
        except LLMRequestError as exc:
            raise InterviewKitGenerationError(str(exc)) from exc

        # source_type/source_text are assigned here, deterministically, by zipping the same
        # ordered grounding list the LLM client's prompt was built from against its returned
        # array by position — this is what guarantees 1:1 grounding rather than trusting the
        # model to echo the source text back correctly.
        must_have_count = len(blueprint.must_have_qualifications)
        questions = []
        for i, draft in enumerate(extraction.questions):
            if i < must_have_count:
                source_type = "must_have"
                source_text = blueprint.must_have_qualifications[i]
            else:
                source_type = "evaluation_criterion"
                source_text = blueprint.evaluation_criteria[i - must_have_count]
            questions.append(
                {
                    "source_type": source_type,
                    "source_text": source_text,
                    "question_text": draft.question_text,
                    "follow_up_prompts": draft.follow_up_prompts,
                }
            )

        kit = await self._repository.upsert(
            company_id=actor.company_id,
            project_id=project_id,
            questions=questions,
            model_used=self._settings.anthropic_model,
            generated_at=datetime.now(timezone.utc),
        )

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="project.interview_kit_generated",
            target_type="project",
            target_id=project_id,
            extra_data={"model": self._settings.anthropic_model},
        )
        return kit

    async def get_kit(self, *, company_id: uuid.UUID, project_id: uuid.UUID) -> InterviewKit:
        kit = await self._repository.get_by_project_id(project_id)
        if kit is None or kit.company_id != company_id or kit.deleted_at is not None:
            raise InterviewKitNotFoundError()
        return kit
