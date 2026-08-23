"""Unit tests for PassportMatchingService's deterministic dimension comparisons
(Location/Compensation/Seniority) -- zero LLM involvement, zero variance, always traceable to the
two real values compared. See app/modules/passport_matching/service.py::_deterministic_dimensions."""

from types import SimpleNamespace

from app.modules.passport_matching.service import _deterministic_dimensions


def _job(**overrides: object) -> SimpleNamespace:
    defaults = {
        "location": None,
        "remote_preference": None,
        "salary_min": None,
        "salary_max": None,
        "seniority": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _dims(passport_snapshot: dict, job: SimpleNamespace) -> dict[str, dict[str, str]]:
    return {d["dimension"]: d for d in _deterministic_dimensions(passport_snapshot, job)}


class TestLocationDimension:
    def test_matching_city_is_strong(self) -> None:
        dims = _dims(
            {"location": "London", "remote_preference": "onsite"},
            _job(location="London", remote_preference="onsite"),
        )
        assert dims["Location"]["rating"] == "Strong"
        assert "London" in dims["Location"]["evidence"]

    def test_mismatched_city_is_weak(self) -> None:
        dims = _dims(
            {"location": "Manchester", "remote_preference": "onsite"},
            _job(location="London", remote_preference="onsite"),
        )
        assert dims["Location"]["rating"] == "Weak"
        assert "London" in dims["Location"]["evidence"]
        assert "Manchester" in dims["Location"]["evidence"]

    def test_either_side_fully_remote_is_strong(self) -> None:
        dims = _dims(
            {"location": "Manchester", "remote_preference": "remote"},
            _job(location="London", remote_preference="onsite"),
        )
        assert dims["Location"]["rating"] == "Strong"

    def test_missing_location_data_is_moderate(self) -> None:
        dims = _dims({"location": None, "remote_preference": None}, _job())
        assert dims["Location"]["rating"] == "Moderate"


class TestCompensationDimension:
    def test_overlapping_ranges_is_strong(self) -> None:
        dims = _dims(
            {"salary_min": 90000, "salary_max": 110000},
            _job(salary_min=100000, salary_max=130000),
        )
        assert dims["Compensation"]["rating"] == "Strong"

    def test_candidate_minimum_above_job_maximum_is_weak(self) -> None:
        dims = _dims(
            {"salary_min": 200000, "salary_max": 220000},
            _job(salary_min=100000, salary_max=130000),
        )
        assert dims["Compensation"]["rating"] == "Weak"
        assert (
            "£100,000" in dims["Compensation"]["evidence"]
            or "£100" in dims["Compensation"]["evidence"]
        )

    def test_unstated_salary_is_moderate(self) -> None:
        dims = _dims(
            {"salary_min": None, "salary_max": None}, _job(salary_min=100000, salary_max=130000)
        )
        assert dims["Compensation"]["rating"] == "Moderate"


class TestSeniorityDimension:
    def test_exact_match_is_strong(self) -> None:
        dims = _dims({"seniority": "Senior"}, _job(seniority="Senior"))
        assert dims["Seniority"]["rating"] == "Strong"

    def test_case_insensitive_match_is_strong(self) -> None:
        dims = _dims({"seniority": "senior"}, _job(seniority="Senior"))
        assert dims["Seniority"]["rating"] == "Strong"

    def test_mismatch_is_weak(self) -> None:
        dims = _dims({"seniority": "Junior"}, _job(seniority="Director"))
        assert dims["Seniority"]["rating"] == "Weak"

    def test_unstated_seniority_is_moderate(self) -> None:
        dims = _dims({"seniority": None}, _job(seniority="Director"))
        assert dims["Seniority"]["rating"] == "Moderate"


def test_every_dimension_has_non_empty_evidence() -> None:
    dims = _deterministic_dimensions(
        {
            "location": "London",
            "remote_preference": "hybrid",
            "salary_min": 90000,
            "salary_max": 110000,
            "seniority": "Senior",
        },
        _job(
            location="London",
            remote_preference="hybrid",
            salary_min=100000,
            salary_max=130000,
            seniority="Senior",
        ),
    )
    assert len(dims) == 3
    for dim in dims:
        assert dim["evidence"]
