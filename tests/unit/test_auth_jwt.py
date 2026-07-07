"""Testes unitários de app.auth.jwt (verificação de JWT do Supabase: HS256 e ES256/JWKS)."""

import base64
import uuid

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from jose import jwt as jose_jwt

from app.auth.jwt import InvalidTokenError, decode_supabase_jwt

pytestmark = pytest.mark.asyncio


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _generate_es256_keypair(kid: str) -> tuple[str, dict]:
    """Gera um par de chaves EC (P-256) e devolve (PEM privada, JWK pública)."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    numbers = private_key.public_key().public_numbers()
    public_jwk = {
        "kty": "EC",
        "crv": "P-256",
        "x": _b64url(numbers.x.to_bytes(32, "big")),
        "y": _b64url(numbers.y.to_bytes(32, "big")),
        "kid": kid,
        "use": "sig",
        "alg": "ES256",
    }
    return private_pem, public_jwk


async def test_decode_valid_hs256_token(monkeypatch):
    from app.auth import jwt as jwt_module

    # Independente do que estiver configurado em `.env`, este teste fixa o
    # segredo explicitamente para não depender do ambiente local.
    monkeypatch.setattr(jwt_module.settings, "supabase_jwt_secret", "")

    user_id = str(uuid.uuid4())
    token = jose_jwt.encode({"sub": user_id, "email": "a@b.com"}, "", algorithm="HS256")
    claims = await decode_supabase_jwt(token)
    assert claims["sub"] == user_id
    assert claims["email"] == "a@b.com"


async def test_decode_invalid_token_raises():
    with pytest.raises(InvalidTokenError):
        await decode_supabase_jwt("not-a-valid-jwt")


async def test_decode_tampered_hs256_signature_raises(monkeypatch):
    from app.auth import jwt as jwt_module

    monkeypatch.setattr(jwt_module.settings, "supabase_jwt_secret", "real-secret")
    token = jose_jwt.encode({"sub": "x"}, "wrong-secret", algorithm="HS256")
    with pytest.raises(InvalidTokenError):
        await decode_supabase_jwt(token)


async def test_decode_es256_token_via_jwks(monkeypatch):
    """Simula um projeto Supabase com 'JWT Signing Keys' (ES256), como no projeto real."""
    from app.auth import jwt as jwt_module

    private_pem, public_jwk = _generate_es256_keypair("test-kid-1")
    user_id = str(uuid.uuid4())
    token = jose_jwt.encode(
        {"sub": user_id, "email": "es256@example.com", "aud": "authenticated"},
        private_pem,
        algorithm="ES256",
        headers={"kid": "test-kid-1"},
    )

    async def fake_get_jwks(force_refresh: bool = False) -> list[dict]:
        return [public_jwk]

    monkeypatch.setattr(jwt_module, "_get_jwks", fake_get_jwks)

    claims = await decode_supabase_jwt(token)
    assert claims["sub"] == user_id
    assert claims["email"] == "es256@example.com"


async def test_decode_es256_unknown_kid_raises(monkeypatch):
    from app.auth import jwt as jwt_module

    private_pem, _ = _generate_es256_keypair("real-kid")
    token = jose_jwt.encode(
        {"sub": "x", "aud": "authenticated"}, private_pem, algorithm="ES256", headers={"kid": "unknown"}
    )

    async def fake_get_jwks(force_refresh: bool = False) -> list[dict]:
        return []

    monkeypatch.setattr(jwt_module, "_get_jwks", fake_get_jwks)

    with pytest.raises(InvalidTokenError):
        await decode_supabase_jwt(token)
