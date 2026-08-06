from app.modules.privacy_gateway.redaction import LINKEDIN_PATTERN, redact_text


def test_redacts_known_email() -> None:
    redacted, counts = redact_text(
        text="Contact me at jane.doe@example.com for more info.", known_full_name=""
    )
    assert "jane.doe@example.com" not in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert counts["email"] == 1


def test_redacts_phone_number() -> None:
    redacted, counts = redact_text(text="Call me at 123-456-7890 anytime.", known_full_name="")
    assert "123-456-7890" not in redacted
    assert "[REDACTED_PHONE]" in redacted
    assert counts["phone"] == 1


def test_does_not_falsely_redact_a_date_range_as_a_phone_number() -> None:
    redacted, counts = redact_text(
        text="Software Engineer at Acme Corp, 2020-2023.", known_full_name=""
    )
    assert "2020-2023" in redacted
    assert counts["phone"] == 0


def test_redacts_linkedin_url() -> None:
    redacted, counts = redact_text(
        text="Profile: https://www.linkedin.com/in/janedoe", known_full_name=""
    )
    assert "linkedin.com/in/janedoe" not in redacted
    assert "[REDACTED_URL]" in redacted
    assert counts["url"] == 1


def test_redacts_known_candidate_name_case_insensitively() -> None:
    redacted, counts = redact_text(
        text="JANE DOE\nSenior Engineer\nReferences available: Jane Doe worked here 2019-2021.",
        known_full_name="Jane Doe",
    )
    assert "Jane Doe" not in redacted
    assert "JANE DOE" not in redacted
    assert counts["name"] == 2


def test_redacts_multiple_pii_categories_together() -> None:
    text = (
        "Jane Doe\n"
        "jane.doe@example.com | 123-456-7890\n"
        "linkedin.com/in/janedoe\n"
        "Experience: Acme Corp, 2020-2023"
    )
    redacted, counts = redact_text(text=text, known_full_name="Jane Doe")
    assert counts == {"name": 1, "address": 0, "url": 1, "email": 1, "phone": 1}
    assert "2020-2023" in redacted


def test_no_pii_present_yields_zero_counts() -> None:
    redacted, counts = redact_text(
        text="Experienced backend engineer with distributed systems background.",
        known_full_name="Someone Else",
    )
    assert counts == {"name": 0, "address": 0, "url": 0, "email": 0, "phone": 0}
    assert redacted == "Experienced backend engineer with distributed systems background."


def test_redacts_us_street_address() -> None:
    redacted, counts = redact_text(
        text="Home address: 123 Maple Street, Springfield, IL 62704", known_full_name=""
    )
    assert "123 Maple Street" not in redacted
    assert "62704" not in redacted
    assert "[REDACTED_ADDRESS]" in redacted
    assert counts["address"] == 2  # street line + city/state/zip tail


def test_redacts_us_street_address_with_apartment() -> None:
    redacted, counts = redact_text(text="456 Oak Ave, Apt 3B, Boston, MA 02108", known_full_name="")
    assert "456 Oak Ave" not in redacted
    assert "Apt 3B" not in redacted
    assert counts["address"] >= 1


def test_redacts_uk_postcode() -> None:
    redacted, counts = redact_text(
        text="Home Address: 42 Baker Street, London, NW1 6XE", known_full_name=""
    )
    assert "42 Baker Street" not in redacted
    assert "NW1 6XE" not in redacted
    assert counts["address"] >= 2


def test_does_not_redact_a_plain_city_name() -> None:
    redacted, counts = redact_text(text="Currently based in Leeds, UK.", known_full_name="")
    assert "Leeds" in redacted
    assert counts["address"] == 0


def test_linkedin_pattern_matches_in_and_pub_profiles() -> None:
    assert LINKEDIN_PATTERN.search("https://www.linkedin.com/in/janedoe")
    assert LINKEDIN_PATTERN.search("linkedin.com/pub/janedoe/12/345/678")


def test_linkedin_pattern_does_not_match_other_sites() -> None:
    assert LINKEDIN_PATTERN.search("https://github.com/janedoe") is None
    assert LINKEDIN_PATTERN.search("https://twitter.com/janedoe") is None
