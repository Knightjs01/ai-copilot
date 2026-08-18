import os

# Must happen before any `app.*` import — app.db.base builds its engine at import time from
# whatever DATABASE_URL is set then, and Settings() is lru_cached, so this has to run first.
_TEST_DB_NAME = "ai_copilot_test"

_original_app_url = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://app_runtime:app_runtime@localhost:5432/ai_copilot",
)
_original_auth_url = os.environ.get(
    "AUTH_DATABASE_URL",
    "postgresql+asyncpg://app_auth:app_auth@localhost:5432/ai_copilot",
)
_original_admin_url = os.environ.get(
    "MIGRATION_DATABASE_URL", "postgresql+asyncpg://copilot:copilot@localhost:5432/ai_copilot"
)

_test_admin_url = _original_admin_url.rsplit("/", 1)[0] + f"/{_TEST_DB_NAME}"

os.environ["DATABASE_URL"] = _original_app_url.rsplit("/", 1)[0] + f"/{_TEST_DB_NAME}"
os.environ["AUTH_DATABASE_URL"] = _original_auth_url.rsplit("/", 1)[0] + f"/{_TEST_DB_NAME}"
os.environ["MIGRATION_DATABASE_URL"] = _test_admin_url
os.environ["ENVIRONMENT"] = "test"  # disables rate limiting — see app/core/rate_limit.py

import asyncio  # noqa: E402
from collections.abc import AsyncGenerator  # noqa: E402
from pathlib import Path  # noqa: E402

import asyncpg  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.modules.candidates.storage import EncryptingFileStorage, LocalFileStorage  # noqa: E402
from app.modules.hiring_blueprint.llm_client import HiringBlueprintExtraction  # noqa: E402
from app.modules.intelligence.llm_client import (  # noqa: E402
    CandidateProfileExtraction,
    EducationEntry,
)
from app.modules.interview_kit.llm_client import (  # noqa: E402
    InterviewKitExtraction,
    InterviewKitQuestionDraft,
)
from app.modules.phantom_passport.llm_client import (  # noqa: E402
    CareerEntryExtraction,
    PassportExtraction,
)
from app.modules.prescreen_assessment.llm_client import AssessmentExtraction  # noqa: E402


def _admin_maintenance_dsn() -> str:
    # asyncpg's native connect() wants a plain postgresql:// DSN, not SQLAlchemy's +asyncpg one,
    # and must point at a database other than the one we're about to create.
    base = _original_admin_url.replace("postgresql+asyncpg://", "postgresql://").rsplit("/", 1)[0]
    return f"{base}/postgres"


async def _ensure_test_database_exists() -> None:
    conn = await asyncpg.connect(_admin_maintenance_dsn())
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", _TEST_DB_NAME)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{_TEST_DB_NAME}"')
    finally:
        await conn.close()


@pytest.fixture(scope="session", autouse=True)
def _setup_test_database() -> None:
    asyncio.run(_ensure_test_database_exists())
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables() -> AsyncGenerator[None, None]:
    yield
    # Uses the admin (copilot) connection, not the app's own app_runtime engine — app_runtime is
    # deliberately not granted TRUNCATE (it's not a privilege the app needs for real operation,
    # only test cleanup), matching the least-privilege grant set from the Phase 1 migration.
    admin_engine = create_async_engine(_test_admin_url)
    try:
        async with admin_engine.begin() as conn:
            # candidate_users is a separate root from companies — it has no FK to companies at
            # all (see app/modules/candidate_auth/__init__.py) — so it needs its own entry here;
            # CASCADE from it transitively covers candidate_refresh_tokens, phantom_passports,
            # passport_personal_info and passport_career_entries.
            await conn.execute(text("TRUNCATE TABLE companies, candidate_users CASCADE"))
    finally:
        await admin_engine.dispose()


class CapturingEmailSender:
    """Test double for app.modules.auth.email.EmailSender — records sent emails instead of
    logging them, so tests can read verification/reset/invite tokens deterministically instead
    of scraping logs (which proved flaky across a full test-suite run with caplog)."""

    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    async def send(self, *, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})


@pytest.fixture
def sent_emails() -> CapturingEmailSender:
    return CapturingEmailSender()


class FakeLLMClient:
    """Test double for app.modules.intelligence.llm_client.LLMClient — returns a canned,
    deterministic extraction instead of calling the real Claude API. No automated test may ever
    hit the real API: it costs money, is slow/flaky over the network, and would require
    ANTHROPIC_API_KEY to be set just to run the test suite at all."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.requirement_calls: list[list[str]] = []

    async def extract_candidate_profile(
        self, *, redacted_text: str, hiring_manager_requirements: list[str]
    ) -> CandidateProfileExtraction:
        self.calls.append(redacted_text)
        self.requirement_calls.append(hiring_manager_requirements)
        return CandidateProfileExtraction(
            skills=["Python", "Distributed Systems"],
            experience_summary="Backend engineer with several years of experience.",
            education=[EducationEntry(institution="Fake University", degree="BSc", field="CS")],
            narrative_summary="A fake but deterministic summary for testing.",
            highlights=["Fake highlight matching a hiring manager requirement."],
        )


@pytest.fixture
def fake_llm_client() -> FakeLLMClient:
    return FakeLLMClient()


class FakeHiringBlueprintLLMClient:
    """Test double for app.modules.hiring_blueprint.llm_client.HiringBlueprintLLMClient —
    returns a canned, deterministic blueprint instead of calling the real Claude API. Kept
    separate from FakeLLMClient (intelligence's fake): different module, different domain,
    different dependency override."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def generate_blueprint(
        self, *, role_brief: str, title: str, department: str | None
    ) -> HiringBlueprintExtraction:
        self.calls.append(role_brief)
        return HiringBlueprintExtraction(
            role_summary="A fake but deterministic role summary for testing.",
            key_responsibilities=["Build things", "Review code"],
            must_have_qualifications=["Fake required skill"],
            nice_to_have_qualifications=["Fake bonus skill"],
            evaluation_criteria=["Technical depth", "Collaboration"],
        )


@pytest.fixture
def fake_hiring_blueprint_llm_client() -> FakeHiringBlueprintLLMClient:
    return FakeHiringBlueprintLLMClient()


class FakeInterviewKitLLMClient:
    """Test double for app.modules.interview_kit.llm_client.InterviewKitLLMClient — returns
    exactly one deterministic question per grounding item, matching the real invariant the
    service enforces (one question per must-have + evaluation-criterion, in order). Kept
    separate from the other fakes: different module, different domain, different dependency
    override."""

    def __init__(self) -> None:
        self.calls: list[tuple[list[str], list[str]]] = []

    async def generate_kit(
        self,
        *,
        role_summary: str,
        must_have_qualifications: list[str],
        evaluation_criteria: list[str],
    ) -> InterviewKitExtraction:
        self.calls.append((must_have_qualifications, evaluation_criteria))
        grounding_items = list(must_have_qualifications) + list(evaluation_criteria)
        return InterviewKitExtraction(
            questions=[
                InterviewKitQuestionDraft(
                    question_text=f"Tell me about a time you demonstrated: {item}",
                    follow_up_prompts=["Fake follow-up prompt"],
                )
                for item in grounding_items
            ]
        )


@pytest.fixture
def fake_interview_kit_llm_client() -> FakeInterviewKitLLMClient:
    return FakeInterviewKitLLMClient()


class FakePrescreenAssessmentLLMClient:
    """Test double for app.modules.prescreen_assessment.llm_client.PrescreenAssessmentLLMClient
    — returns canned, deterministic responses instead of calling the real Claude API. Kept
    separate from the other two fakes: different module, different domain, different
    dependency override."""

    def __init__(self) -> None:
        self.assessment_calls: list[list[str]] = []
        self.handoff_calls: list[str] = []

    async def generate_assessment(
        self,
        *,
        role_summary: str,
        must_have_qualifications: list[str],
        evaluation_criteria: list[str],
        top_requirements: list[str],
        candidate_skills: list[str],
        candidate_experience_summary: str,
        candidate_education: list[dict[str, str]],
    ) -> AssessmentExtraction:
        self.assessment_calls.append(top_requirements)
        return AssessmentExtraction(
            fit_rating="Good Fit",
            fit_summary="A fake but deterministic fit summary for testing.",
            strengths=["Fake strength"],
            gaps=["Fake gap"],
            suggested_questions=["Fake suggested question"],
            areas_to_probe=["Fake area to probe"],
        )

    async def generate_handoff_recommendations(
        self, *, fit_summary: str, gaps: list[str], areas_to_probe: list[str], prescreen_notes: str
    ) -> list[str]:
        self.handoff_calls.append(prescreen_notes)
        return ["Fake handoff recommendation"]


@pytest.fixture
def fake_prescreen_assessment_llm_client() -> FakePrescreenAssessmentLLMClient:
    return FakePrescreenAssessmentLLMClient()


class FakePassportLLMClient:
    """Test double for app.modules.phantom_passport.llm_client.LLMClient — returns a canned,
    deterministic Passport extraction instead of calling the real Claude API."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.summary_suggestion_calls: list[str] = []
        self.skills_suggestion_calls: list[list[str]] = []
        self.industries_suggestion_calls: list[list[str]] = []

    async def extract_passport_from_cv(self, *, redacted_text: str) -> PassportExtraction:
        self.calls.append(redacted_text)
        return PassportExtraction(
            headline="Senior Product Leader",
            seniority="Senior",
            years_experience=12,
            summary="A fake but deterministic professional summary for testing.",
            skills=["Product Strategy", "Team Leadership"],
            industries=["FinTech", "B2B SaaS"],
            career_entries=[
                CareerEntryExtraction(
                    title="VP Product",
                    company_name="Stripe",
                    company_name_anonymized="Global Payments Platform",
                    is_current=True,
                    responsibilities="Led product strategy for the platform.",
                    achievements=["Scaled product org from 12 to 40"],
                )
            ],
        )

    async def suggest_summary_improvement(
        self, *, headline: str | None, summary: str, skills: list[str]
    ) -> str:
        self.summary_suggestion_calls.append(summary)
        return "A fake but deterministic improved summary for testing."

    async def suggest_skills(
        self, *, headline: str | None, summary: str | None, existing_skills: list[str]
    ) -> list[str]:
        self.skills_suggestion_calls.append(existing_skills)
        return ["Fake suggested skill"]

    async def suggest_industries(
        self, *, headline: str | None, summary: str | None, existing_industries: list[str]
    ) -> list[str]:
        self.industries_suggestion_calls.append(existing_industries)
        return ["Fake suggested industry"]


@pytest.fixture
def fake_passport_llm_client() -> FakePassportLLMClient:
    return FakePassportLLMClient()


@pytest.fixture
def test_storage(tmp_path: Path) -> EncryptingFileStorage:
    # Own temp directory per test, not the shared dev storage_dir — otherwise every test run
    # leaves orphaned resume files under backend/storage/ on the host indefinitely. Exposed as
    # its own fixture (not just built inline in `client`) so tests can inspect the filesystem
    # directly — e.g. project_deletion's tests asserting a resume file was actually removed.
    # Wrapped in EncryptingFileStorage so tests exercise the real production storage path
    # (encrypted at rest) rather than silently bypassing it — see
    # app.modules.candidates.storage.EncryptingFileStorage. A test wanting the raw ciphertext on
    # disk reads directly from `tmp_path / "storage"` (same convention used here) rather than
    # going through this fixture, which always transparently decrypts on read.
    return EncryptingFileStorage(LocalFileStorage(root=str(tmp_path / "storage")))


@pytest_asyncio.fixture
async def client(
    sent_emails: CapturingEmailSender,
    fake_llm_client: FakeLLMClient,
    fake_hiring_blueprint_llm_client: FakeHiringBlueprintLLMClient,
    fake_interview_kit_llm_client: FakeInterviewKitLLMClient,
    fake_prescreen_assessment_llm_client: FakePrescreenAssessmentLLMClient,
    fake_passport_llm_client: FakePassportLLMClient,
    test_storage: EncryptingFileStorage,
) -> AsyncGenerator[AsyncClient, None]:
    from app.main import app
    from app.modules.auth.dependencies import get_email_sender
    from app.modules.candidates.dependencies import get_file_storage
    from app.modules.hiring_blueprint.dependencies import get_hiring_blueprint_llm_client
    from app.modules.intelligence.dependencies import get_llm_client
    from app.modules.interview_kit.dependencies import get_interview_kit_llm_client
    from app.modules.phantom_passport.dependencies import (
        get_llm_client as get_passport_llm_client,
    )
    from app.modules.prescreen_assessment.dependencies import get_prescreen_assessment_llm_client

    app.dependency_overrides[get_email_sender] = lambda: sent_emails
    app.dependency_overrides[get_file_storage] = lambda: test_storage
    app.dependency_overrides[get_llm_client] = lambda: fake_llm_client
    app.dependency_overrides[get_hiring_blueprint_llm_client] = (
        lambda: fake_hiring_blueprint_llm_client
    )
    app.dependency_overrides[get_interview_kit_llm_client] = lambda: fake_interview_kit_llm_client
    app.dependency_overrides[get_prescreen_assessment_llm_client] = (
        lambda: fake_prescreen_assessment_llm_client
    )
    app.dependency_overrides[get_passport_llm_client] = lambda: fake_passport_llm_client
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(get_email_sender, None)
        app.dependency_overrides.pop(get_file_storage, None)
        app.dependency_overrides.pop(get_llm_client, None)
        app.dependency_overrides.pop(get_hiring_blueprint_llm_client, None)
        app.dependency_overrides.pop(get_interview_kit_llm_client, None)
        app.dependency_overrides.pop(get_prescreen_assessment_llm_client, None)
        app.dependency_overrides.pop(get_passport_llm_client, None)
