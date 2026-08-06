import re
import uuid

import pytest

from app.modules.identity_vault.exceptions import CallsignGenerationExhaustedError
from app.modules.identity_vault.service import IdentityVaultService

_CALLSIGN_RE = re.compile(r"^[A-Za-z]+-\d{2}$")


class _FixedResultCandidateRepo:
    """Stub swapped in for IdentityVaultService._candidates_repo — the real repository needs a
    live DB session, but generate_callsign only ever calls callsign_exists_in_project on it."""

    def __init__(self, results: list[bool]) -> None:
        self._results = list(results)

    async def callsign_exists_in_project(self, project_id: uuid.UUID, callsign: str) -> bool:
        return self._results.pop(0) if self._results else False


def _service_with_stubbed_candidates(results: list[bool]) -> IdentityVaultService:
    # __init__ never touches the DB (it just stores the session and constructs sub-repositories
    # that also only store the session), so a None session is safe for a pure unit test as long
    # as the method under test doesn't reach any real repository/service.
    service = IdentityVaultService(None)  # type: ignore[arg-type]
    service._candidates_repo = _FixedResultCandidateRepo(results)  # type: ignore[assignment]
    return service


async def test_generate_callsign_format() -> None:
    service = _service_with_stubbed_candidates([])
    callsign = await service.generate_callsign(project_id=uuid.uuid4())
    assert _CALLSIGN_RE.match(callsign), callsign


async def test_generate_callsign_retries_on_collision() -> None:
    service = _service_with_stubbed_candidates([True, True, False])
    callsign = await service.generate_callsign(project_id=uuid.uuid4())
    assert _CALLSIGN_RE.match(callsign), callsign


async def test_generate_callsign_exhausts_after_max_attempts() -> None:
    service = _service_with_stubbed_candidates([True, True, True, True, True])
    with pytest.raises(CallsignGenerationExhaustedError):
        await service.generate_callsign(project_id=uuid.uuid4())
