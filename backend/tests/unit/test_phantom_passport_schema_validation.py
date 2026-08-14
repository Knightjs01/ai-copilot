"""Adversarial: PassportUpdate's freeform fields feed both an LLM prompt (career-coaching /
matching features) and encrypted storage — task #211 found several of them had no max_length,
unlike sibling fields on the same schema (headline, seniority, legal_name, phone, address).
Fixed alongside this test in app/modules/phantom_passport/schemas.py rather than shipped as a
"currently accepts unbounded input" regression test — see that file's _ShortListItem alias and
the per-field Field(max_length=...) additions.
"""

import pytest
from pydantic import ValidationError

from app.modules.phantom_passport.schemas import CareerEntryInput, PassportUpdate, PersonalInfoInput

_VALID_PERSONAL_INFO = {"legal_name": "Jamie Candidate"}
_VALID_CAREER_ENTRY = {
    "title": "VP Product",
    "company_name": "Stripe",
    "company_name_anonymized": "Global Payments Platform",
}


def test_oversized_summary_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PassportUpdate(summary="x" * 5001, personal_info=PersonalInfoInput(**_VALID_PERSONAL_INFO))


def test_summary_at_the_limit_is_accepted() -> None:
    PassportUpdate(summary="x" * 5000, personal_info=PersonalInfoInput(**_VALID_PERSONAL_INFO))


def test_oversized_single_skill_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PassportUpdate(skills=["x" * 201], personal_info=PersonalInfoInput(**_VALID_PERSONAL_INFO))


def test_too_many_skills_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PassportUpdate(
            skills=["Python"] * 101, personal_info=PersonalInfoInput(**_VALID_PERSONAL_INFO)
        )


def test_oversized_single_industry_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PassportUpdate(
            industries=["x" * 201], personal_info=PersonalInfoInput(**_VALID_PERSONAL_INFO)
        )


def test_oversized_remote_preference_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PassportUpdate(
            remote_preference="x" * 101, personal_info=PersonalInfoInput(**_VALID_PERSONAL_INFO)
        )


def test_oversized_notice_period_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PassportUpdate(
            notice_period="x" * 101, personal_info=PersonalInfoInput(**_VALID_PERSONAL_INFO)
        )


def test_oversized_career_intent_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PassportUpdate(
            career_intent="x" * 101, personal_info=PersonalInfoInput(**_VALID_PERSONAL_INFO)
        )


def test_too_many_career_entries_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PassportUpdate(
            personal_info=PersonalInfoInput(**_VALID_PERSONAL_INFO),
            career_entries=[CareerEntryInput(**_VALID_CAREER_ENTRY) for _ in range(51)],
        )


def test_oversized_career_entry_responsibilities_is_rejected() -> None:
    with pytest.raises(ValidationError):
        CareerEntryInput(**_VALID_CAREER_ENTRY, responsibilities="x" * 5001)


def test_oversized_career_entry_achievement_is_rejected() -> None:
    with pytest.raises(ValidationError):
        CareerEntryInput(**_VALID_CAREER_ENTRY, achievements=["x" * 201])


def test_too_many_career_entry_achievements_is_rejected() -> None:
    with pytest.raises(ValidationError):
        CareerEntryInput(**_VALID_CAREER_ENTRY, achievements=["Shipped a thing"] * 51)


def test_valid_passport_update_with_typical_field_lengths_is_accepted() -> None:
    PassportUpdate(
        headline="Senior Product Leader",
        seniority="Senior",
        summary="A senior product leader with a track record of shipping.",
        skills=["Product Strategy", "Team Leadership"],
        industries=["FinTech", "B2B SaaS"],
        remote_preference="hybrid",
        notice_period="one_month",
        career_intent="actively_looking",
        personal_info=PersonalInfoInput(**_VALID_PERSONAL_INFO),
        career_entries=[
            CareerEntryInput(
                **_VALID_CAREER_ENTRY,
                responsibilities="Led product strategy for the platform.",
                achievements=["Scaled product org from 12 to 40"],
            )
        ],
    )
