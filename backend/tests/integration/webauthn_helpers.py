"""A hand-built virtual FIDO2 authenticator for exercising the real py_webauthn verification
functions end-to-end (see app/core/webauthn.py) without needing an actual security key or
platform authenticator in CI. Validated during development against verify_registration_response
and verify_authentication_response directly before being wired into the integration tests below
— it produces byte-for-byte spec-shaped attestationObject/authenticatorData/clientDataJSON, not
a mock of the verification result."""

import hashlib
import json
import os
import struct

import cbor2
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from webauthn.helpers import bytes_to_base64url

RP_ID = "localhost"
ORIGIN = "http://localhost:3000"


class VirtualAuthenticator:
    def __init__(self) -> None:
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.credential_id = os.urandom(32)
        self.sign_count = 0

    def cose_public_key(self) -> bytes:
        numbers = self.private_key.public_key().public_numbers()
        x = numbers.x.to_bytes(32, "big")
        y = numbers.y.to_bytes(32, "big")
        cose = {1: 2, 3: -7, -1: 1, -2: x, -3: y}
        return cbor2.dumps(cose)

    def _auth_data(self, *, attested: bool) -> bytes:
        rp_id_hash = hashlib.sha256(RP_ID.encode()).digest()
        flags = 0b00000001
        if attested:
            flags |= 0b01000000
        self.sign_count += 1
        sign_count_bytes = struct.pack(">I", self.sign_count)
        auth_data = rp_id_hash + bytes([flags]) + sign_count_bytes
        if attested:
            aaguid = b"\x00" * 16
            cred_id_len = struct.pack(">H", len(self.credential_id))
            auth_data += aaguid + cred_id_len + self.credential_id + self.cose_public_key()
        return auth_data

    def register(self, challenge: bytes) -> dict:
        client_data = {
            "type": "webauthn.create",
            "challenge": bytes_to_base64url(challenge),
            "origin": ORIGIN,
        }
        client_data_json = json.dumps(client_data).encode()
        auth_data = self._auth_data(attested=True)
        attestation_object = cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": auth_data})
        return {
            "id": bytes_to_base64url(self.credential_id),
            "rawId": bytes_to_base64url(self.credential_id),
            "type": "public-key",
            "response": {
                "clientDataJSON": bytes_to_base64url(client_data_json),
                "attestationObject": bytes_to_base64url(attestation_object),
            },
            "clientExtensionResults": {},
        }

    def authenticate(self, challenge: bytes) -> dict:
        client_data = {
            "type": "webauthn.get",
            "challenge": bytes_to_base64url(challenge),
            "origin": ORIGIN,
        }
        client_data_json = json.dumps(client_data).encode()
        auth_data = self._auth_data(attested=False)
        client_data_hash = hashlib.sha256(client_data_json).digest()
        signature = self.private_key.sign(auth_data + client_data_hash, ec.ECDSA(hashes.SHA256()))
        return {
            "id": bytes_to_base64url(self.credential_id),
            "rawId": bytes_to_base64url(self.credential_id),
            "type": "public-key",
            "response": {
                "clientDataJSON": bytes_to_base64url(client_data_json),
                "authenticatorData": bytes_to_base64url(auth_data),
                "signature": bytes_to_base64url(signature),
                "userHandle": None,
            },
            "clientExtensionResults": {},
        }
