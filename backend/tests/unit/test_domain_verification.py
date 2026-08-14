from app.modules.companies.domain_verification import extract_email_domain, is_verified_domain


def test_extract_email_domain_lowercases_and_strips() -> None:
    assert extract_email_domain("Owner@RealCompany.COM ") == "realcompany.com"


def test_corporate_domain_is_verified() -> None:
    assert is_verified_domain("realcompany.com") is True


def test_free_email_domain_is_not_verified() -> None:
    assert is_verified_domain("gmail.com") is False
    assert is_verified_domain("outlook.com") is False
    assert is_verified_domain("icloud.com") is False
