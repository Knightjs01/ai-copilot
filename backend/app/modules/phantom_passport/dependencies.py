from app.modules.phantom_passport.llm_client import AnthropicLLMClient, LLMClient

_default_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Overridable via app.dependency_overrides — tests inject a FakeLLMClient. Constructed
    lazily so importing this module (which happens regardless of overrides, via api.py ->
    main.py) never eagerly touches ANTHROPIC_API_KEY. Same pattern as
    intelligence/dependencies.py."""

    global _default_client
    if _default_client is None:
        _default_client = AnthropicLLMClient()
    return _default_client
