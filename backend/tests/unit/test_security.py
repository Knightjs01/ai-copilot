import time
import uuid

import jwt
import pytest

from app.modules.auth import security


def test_password_hash_and_verify_roundtrip() -> None:
    hashed = security.hash_password("correct horse battery staple")
    assert security.verify_password("correct horse battery staple", hashed)
    assert not security.verify_password("wrong password", hashed)


def test_access_token_roundtrip() -> None:
    user_id = uuid.uuid4()
    company_id = uuid.uuid4()
    token = security.create_access_token(user_id=user_id, company_id=company_id)

    payload = security.decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["company_id"] == str(company_id)


def test_decode_access_token_rejects_garbage() -> None:
    with pytest.raises(security.TokenError):
        security.decode_access_token("not-a-real-token")


def test_decode_access_token_rejects_expired_token(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = security.get_settings()
    token = jwt.encode(
        {"sub": "x", "company_id": "y", "exp": time.time() - 10},
        settings.secret_key,
        algorithm=security.JWT_ALGORITHM,
    )
    with pytest.raises(security.TokenError):
        security.decode_access_token(token)


def test_mfa_challenge_token_has_distinct_scope() -> None:
    user_id = uuid.uuid4()
    token = security.create_mfa_challenge_token(user_id=user_id)
    payload = security.decode_mfa_challenge_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["scope"] == "mfa_challenge"

    with pytest.raises(security.TokenError):
        # A normal access token should not pass as an MFA challenge token.
        security.decode_mfa_challenge_token(
            security.create_access_token(user_id=user_id, company_id=uuid.uuid4())
        )


def test_totp_generate_and_verify() -> None:
    secret = security.generate_totp_secret()
    uri = security.get_totp_provisioning_uri(secret=secret, email="user@example.com")
    assert "otpauth://totp/" in uri

    import pyotp

    code = pyotp.TOTP(secret).now()
    assert security.verify_totp_code(secret=secret, code=code)
    assert not security.verify_totp_code(secret=secret, code="000000")


def test_fernet_encrypt_decrypt_roundtrip() -> None:
    plain = "JBSWY3DPEHPK3PXP"
    encrypted = security.encrypt_secret(plain)
    assert encrypted != plain
    assert security.decrypt_secret(encrypted) == plain


def test_fernet_decrypt_rejects_tampered_value() -> None:
    encrypted = security.encrypt_secret("some-secret")
    with pytest.raises(security.TokenError):
        security.decrypt_secret(encrypted[:-4] + "abcd")


def test_opaque_token_hash_is_deterministic_and_not_reversible() -> None:
    token = security.generate_opaque_token()
    assert security.hash_opaque_token(token) == security.hash_opaque_token(token)
    assert security.hash_opaque_token(token) != token
