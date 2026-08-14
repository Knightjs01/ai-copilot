import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings
from app.core.key_provider import get_key_provider

_password_hasher = PasswordHasher()

JWT_ALGORITHM = "HS256"


def hash_password(plain_password: str) -> str:
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


class TokenError(Exception):
    pass


def create_access_token(*, user_id: uuid.UUID, company_id: uuid.UUID) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "company_id": str(company_id),
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def create_candidate_access_token(*, candidate_id: uuid.UUID) -> str:
    """Candidates are a separate principal from company Users — no company_id, because a
    Phantom Passport is owned by the candidate directly and exists independently of any single
    company's tenant. scope="candidate" is what get_current_candidate (candidate_auth.dependencies)
    checks to make sure a company User's access token can never be replayed against a candidate
    route, and vice versa — decode_access_token below is generic enough to decode either."""

    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(candidate_id),
        "scope": "candidate",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc


def create_mfa_challenge_token(*, user_id: uuid.UUID) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "scope": "mfa_challenge",
        "iat": now,
        "exp": now + timedelta(minutes=settings.mfa_challenge_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def decode_mfa_challenge_token(token: str) -> dict[str, Any]:
    payload = decode_access_token(token)
    if payload.get("scope") != "mfa_challenge":
        raise TokenError("Not an MFA challenge token")
    return payload


def create_candidate_mfa_challenge_token(*, candidate_id: uuid.UUID) -> str:
    # A distinct scope from create_mfa_challenge_token's "mfa_challenge" — without it, a
    # candidate's challenge token would decode successfully at the company /auth/mfa/verify
    # endpoint (and vice versa) any time a candidate_id happened to collide with a company
    # user_id, since both are just UUIDs in the same token format.
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(candidate_id),
        "scope": "candidate_mfa_challenge",
        "iat": now,
        "exp": now + timedelta(minutes=settings.mfa_challenge_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def decode_candidate_mfa_challenge_token(token: str) -> dict[str, Any]:
    payload = decode_access_token(token)
    if payload.get("scope") != "candidate_mfa_challenge":
        raise TokenError("Not a candidate MFA challenge token")
    return payload


def create_step_up_token(*, user_id: uuid.UUID) -> str:
    """Proof that the holder of a valid access token has, moments ago, also re-supplied their
    password (and MFA code, if enrolled) — see auth.service.auth_service.AuthService.step_up
    and auth.dependencies.require_step_up. An access token alone proves "this session is
    authenticated"; a step-up token additionally proves "the actual person is at the keyboard
    right now", which is the bar high-risk actions (identity reveal, project purge, admin
    invite) need — a stolen bearer token by itself is not enough to perform them."""

    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "scope": "step_up",
        "iat": now,
        "exp": now + timedelta(minutes=settings.step_up_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def decode_step_up_token(token: str) -> dict[str, Any]:
    payload = decode_access_token(token)
    if payload.get("scope") != "step_up":
        raise TokenError("Not a step-up token")
    return payload


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_totp_provisioning_uri(
    *, secret: str, email: str, issuer: str = "AI Interview Copilot"
) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)


def verify_totp_code(*, secret: str, code: str) -> bool:
    return pyotp.totp.TOTP(secret).verify(code, valid_window=1)


def _fernet() -> Fernet:
    return Fernet(get_key_provider().get_key())


def encrypt_secret(plain_value: str) -> str:
    return _fernet().encrypt(plain_value.encode()).decode()


def decrypt_secret(encrypted_value: str) -> str:
    try:
        return _fernet().decrypt(encrypted_value.encode()).decode()
    except InvalidToken as exc:
        raise TokenError("Could not decrypt secret") from exc


def generate_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def hash_opaque_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# Excludes visually ambiguous characters (0/O, 1/I/L) — these are meant to be hand-typed from a
# printed/saved list during account recovery, not copy-pasted.
_BACKUP_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def generate_backup_code() -> str:
    """A single MFA recovery code, formatted XXXXX-XXXXX for readability. High-entropy (32^10 ≈
    2^50 possibilities) — hashed the same way as opaque tokens, never a candidate for slow
    password hashing since it's random, not user-chosen."""

    chars = [secrets.choice(_BACKUP_CODE_ALPHABET) for _ in range(10)]
    return "".join(chars[:5]) + "-" + "".join(chars[5:])
