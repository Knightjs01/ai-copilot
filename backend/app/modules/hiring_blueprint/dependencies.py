from app.modules.hiring_blueprint.llm_client import (
    AnthropicHiringBlueprintLLMClient,
    HiringBlueprintLLMClient,
)

_default_client: HiringBlueprintLLMClient | None = None


def get_hiring_blueprint_llm_client() -> HiringBlueprintLLMClient:
    """Overridable via app.dependency_overrides — tests inject a FakeHiringBlueprintLLMClient
    instead of calling the real Claude API, same pattern as intelligence's get_llm_client.

    Constructed lazily (on first real call), not at module import time — see
    app/modules/intelligence/dependencies.py for the full reasoning (an eager module-level
    instance would crash every test's `from app.main import app` when ANTHROPIC_API_KEY is
    unset, which it always is in CI/tests).
    """

    global _default_client
    if _default_client is None:
        _default_client = AnthropicHiringBlueprintLLMClient()
    return _default_client
