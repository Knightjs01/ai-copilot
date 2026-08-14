"""Thin wrapper around the `webauthn` (py_webauthn) library's registration/authentication
ceremonies, parametrized by this app's relying-party settings. Shared by both principals
(company User and CandidateUser) — see auth/service/auth_service.py and
candidate_auth/service.py for how each wires this into their own credential storage, since the
two have separate tables (webauthn_credentials vs candidate_webauthn_credentials) for the same
reason every other per-principal table in this app is split: candidates have no company_id / no
tenant to scope, so RLS applies to one and not the other.

A passkey is treated as satisfying this app's mandatory-MFA requirement on its own — see
mfa_policy.py — because a passkey ceremony is inherently two-factor (possession of the
authenticator + the biometric/PIN unlock gating it), the same reasoning that makes WebAuthn a
first-class phishing-resistant credential rather than "yet another OTP".
"""

import base64
import uuid
from dataclasses import dataclass
from typing import Any

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.authentication.verify_authentication_response import VerifiedAuthentication
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.exceptions import WebAuthnException
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)
from webauthn.registration.verify_registration_response import VerifiedRegistration

from app.core.config import get_settings


def encode_credential_id(raw: bytes) -> str:
    """Base64url, matching the encoding a client sends `id`/`rawId` in — stored this way so a
    credential lookup at authentication time is a direct string match, no re-encoding needed."""
    return bytes_to_base64url(raw)


def decode_credential_id(encoded: str) -> bytes:
    return base64url_to_bytes(encoded)


def encode_public_key(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


def decode_public_key(encoded: str) -> bytes:
    return base64.b64decode(encoded)


class WebAuthnVerificationError(Exception):
    """Raised for any ceremony failure — wrong challenge, signature mismatch, malformed
    response, replayed sign count. Deliberately one error type: the caller (an HTTP endpoint)
    should treat every failure mode the same way (401), not branch on which library exception
    fired, since none of that detail is actionable or safe to hand back to the client."""


@dataclass
class RegistrationCeremony:
    options_json: str
    challenge: bytes


@dataclass
class AuthenticationCeremony:
    options_json: str
    challenge: bytes


def begin_registration(
    *,
    user_id: uuid.UUID,
    user_name: str,
    user_display_name: str,
    exclude_credential_ids: list[bytes],
) -> RegistrationCeremony:
    settings = get_settings()
    options = generate_registration_options(
        rp_id=settings.webauthn_rp_id,
        rp_name=settings.webauthn_rp_name,
        user_id=user_id.bytes,
        user_name=user_name,
        user_display_name=user_display_name,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=cred_id) for cred_id in exclude_credential_ids
        ],
    )
    return RegistrationCeremony(options_json=options_to_json(options), challenge=options.challenge)


def verify_registration(
    *, credential_json: dict[str, Any], expected_challenge: bytes
) -> VerifiedRegistration:
    settings = get_settings()
    try:
        return verify_registration_response(
            credential=credential_json,
            expected_challenge=expected_challenge,
            expected_rp_id=settings.webauthn_rp_id,
            expected_origin=settings.webauthn_origin,
        )
    except WebAuthnException as exc:
        raise WebAuthnVerificationError(str(exc)) from exc


def begin_authentication(*, allow_credential_ids: list[bytes]) -> AuthenticationCeremony:
    """allow_credential_ids may be empty — the caller (e.g. the pre-login options endpoint for
    an email that turns out not to exist) still gets back a plausible-looking challenge so the
    response shape can't be used to enumerate accounts, mirroring the anti-enumeration principle
    in login_throttle.py."""

    settings = get_settings()
    options = generate_authentication_options(
        rp_id=settings.webauthn_rp_id,
        allow_credentials=[
            PublicKeyCredentialDescriptor(id=cred_id) for cred_id in allow_credential_ids
        ],
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    return AuthenticationCeremony(
        options_json=options_to_json(options), challenge=options.challenge
    )


def verify_authentication(
    *,
    credential_json: dict[str, Any],
    expected_challenge: bytes,
    public_key: bytes,
    sign_count: int,
) -> VerifiedAuthentication:
    settings = get_settings()
    try:
        return verify_authentication_response(
            credential=credential_json,
            expected_challenge=expected_challenge,
            expected_rp_id=settings.webauthn_rp_id,
            expected_origin=settings.webauthn_origin,
            credential_public_key=public_key,
            credential_current_sign_count=sign_count,
        )
    except WebAuthnException as exc:
        raise WebAuthnVerificationError(str(exc)) from exc
