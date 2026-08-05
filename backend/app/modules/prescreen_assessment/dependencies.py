from app.modules.prescreen_assessment.llm_client import (
    AnthropicPrescreenAssessmentLLMClient,
    PrescreenAssessmentLLMClient,
)

_default_client: PrescreenAssessmentLLMClient | None = None


def get_prescreen_assessment_llm_client() -> PrescreenAssessmentLLMClient:
    """Overridable via app.dependency_overrides — tests inject a
    FakePrescreenAssessmentLLMClient instead of calling the real Claude API, same pattern as
    the other two LLM modules' get_*_llm_client().

    Constructed lazily (on first real call), not at module import time — see
    app/modules/intelligence/dependencies.py for the full reasoning (an eager module-level
    instance would crash every test's `from app.main import app` when ANTHROPIC_API_KEY is
    unset, which it always is in CI/tests).
    """

    global _default_client
    if _default_client is None:
        _default_client = AnthropicPrescreenAssessmentLLMClient()
    return _default_client
