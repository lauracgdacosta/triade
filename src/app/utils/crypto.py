"""Criptografia simétrica (Fernet) para segredos armazenados no banco.

Usado para cifrar access/refresh tokens de integrações de terceiros (ex.:
Google Calendar) em repouso — sem isso, um vazamento do banco daria acesso
permanente à agenda do usuário via o refresh_token em texto puro.
"""

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


class CryptoError(Exception):
    pass


@lru_cache
def _get_fernet() -> Fernet:
    key = get_settings().google_token_encryption_key
    if not key:
        raise CryptoError(
            "GOOGLE_TOKEN_ENCRYPTION_KEY não configurada. Gere uma com "
            "`python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"`."
        )
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise CryptoError("GOOGLE_TOKEN_ENCRYPTION_KEY inválida — precisa ser uma chave Fernet válida.") from exc


def encrypt(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    try:
        return _get_fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise CryptoError("Token cifrado inválido ou corrompido.") from exc
