"""Abstraction over where symmetric encryption keys come from, so the app can run today on a
single static key (StaticEnvKeyProvider) and later swap in a real KMS-backed provider (AWS KMS,
GCP Cloud KMS, Azure Key Vault, HashiCorp Vault) without touching any of the call sites that
encrypt/decrypt PII — identity vault fields, phantom passport personal info, MFA secrets — all of
which go through app.modules.auth.security.encrypt_secret/decrypt_secret, which in turn goes
through get_key_provider() here. Swapping providers is a one-file change.

Design notes for the future KMS provider (deliberately not implemented — no KMS is provisioned
yet; see the "design interfaces, stub the rest" decision):
- Real KMS services don't hand out raw key material for bulk local use; the standard pattern is
  envelope encryption — call the KMS's GenerateDataKey API to get a fresh Data Encryption Key
  (DEK) returned both in plaintext and as KMS-encrypted bytes, decrypt the DEK once per process
  via a KMS API call (or on a bounded TTL), cache the plaintext DEK in memory, and use it locally
  for the actual Fernet operations — you do not call out to the KMS for every field encrypted.
- Key rotation: a KmsKeyProvider needs to retain old DEKs (keyed by key_id) so it can still
  decrypt values encrypted before a rotation. get_key()'s key_id parameter exists for that; the
  stub provider ignores it and always returns its single key, since it never rotates.
- current_key_id() is what a caller would persist alongside newly-encrypted ciphertext if this
  app ever needs to know which key encrypted which value (it doesn't today — Fernet tokens are
  self-contained and there is only ever one active key). Wiring that through is future work that
  only matters once a second key version actually exists.
"""

from typing import Protocol


class KeyProvider(Protocol):
    def current_key_id(self) -> str:
        """Identifies which key new encryptions should use."""
        ...

    def get_key(self, key_id: str | None = None) -> bytes:
        """Raw key material for key_id, or the current key if key_id is None."""
        ...


class StaticEnvKeyProvider:
    """Today's actual behavior end to end: one Fernet key from settings.encryption_key, forever.
    No rotation, no per-tenant keys — this is the "stub" half of "design interfaces, stub the
    rest" until real KMS infrastructure exists."""

    _KEY_ID = "static-v1"

    def __init__(self, key: str) -> None:
        self._key = key.encode()

    def current_key_id(self) -> str:
        return self._KEY_ID

    def get_key(self, key_id: str | None = None) -> bytes:
        return self._key


_key_provider: KeyProvider | None = None


def get_key_provider() -> KeyProvider:
    global _key_provider
    if _key_provider is None:
        from app.core.config import get_settings

        _key_provider = StaticEnvKeyProvider(get_settings().encryption_key)
    return _key_provider


def set_key_provider(provider: KeyProvider | None) -> None:
    """Test/override hook. encrypt_secret/decrypt_secret are called deep inside service code,
    not directly from a FastAPI endpoint signature, so there's no Depends() seam for
    app.dependency_overrides to hook into the way get_email_sender() or get_file_storage() do —
    this module-level setter is the equivalent for encryption."""
    global _key_provider
    _key_provider = provider
