from cryptography.fernet import Fernet

from app.core.key_provider import StaticEnvKeyProvider, get_key_provider, set_key_provider
from app.modules.auth import security


def test_static_provider_returns_a_usable_fernet_key() -> None:
    key = Fernet.generate_key().decode()
    provider = StaticEnvKeyProvider(key)
    assert provider.get_key() == key.encode()
    assert provider.current_key_id() == "static-v1"


def test_static_provider_ignores_key_id_argument() -> None:
    key = Fernet.generate_key().decode()
    provider = StaticEnvKeyProvider(key)
    assert provider.get_key("some-other-key-id") == provider.get_key()


def test_encrypt_secret_round_trips_through_an_overridden_key_provider() -> None:
    original = get_key_provider()
    try:
        set_key_provider(StaticEnvKeyProvider(Fernet.generate_key().decode()))
        ciphertext = security.encrypt_secret("a secret value")
        assert ciphertext != "a secret value"
        assert security.decrypt_secret(ciphertext) == "a secret value"
    finally:
        set_key_provider(original)


def test_decrypt_fails_after_swapping_to_a_different_key() -> None:
    original = get_key_provider()
    try:
        set_key_provider(StaticEnvKeyProvider(Fernet.generate_key().decode()))
        ciphertext = security.encrypt_secret("a secret value")

        set_key_provider(StaticEnvKeyProvider(Fernet.generate_key().decode()))
        try:
            security.decrypt_secret(ciphertext)
            raised = False
        except security.TokenError:
            raised = True
        assert raised
    finally:
        set_key_provider(original)
