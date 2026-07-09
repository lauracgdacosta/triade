"""Testes do módulo de criptografia (tokens do Google Calendar em repouso)."""

import pytest

from app.config import get_settings
from app.utils import crypto


def test_encrypt_decrypt_roundtrip():
    ciphertext = crypto.encrypt("meu-refresh-token")
    assert ciphertext != "meu-refresh-token"
    assert crypto.decrypt(ciphertext) == "meu-refresh-token"


def test_decrypt_invalid_token_raises_crypto_error():
    with pytest.raises(crypto.CryptoError):
        crypto.decrypt("isto-nao-e-um-token-fernet-valido")


def test_missing_key_raises_clear_error():
    settings = get_settings()
    original = settings.google_token_encryption_key
    crypto._get_fernet.cache_clear()
    settings.google_token_encryption_key = ""
    try:
        with pytest.raises(crypto.CryptoError):
            crypto.encrypt("x")
    finally:
        settings.google_token_encryption_key = original
        crypto._get_fernet.cache_clear()
