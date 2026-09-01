"""Hash de senha (bcrypt) e emissão/validação de tokens JWT."""
from __future__ import annotations

import datetime as dt
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

_BCRYPT_MAX_BYTES = 72  # limite do algoritmo bcrypt


def hash_password(password: str) -> str:
    pw = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        pw = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
        return bcrypt.checkpw(pw, password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(subject: str | int, extra: dict[str, Any] | None = None) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + dt.timedelta(minutes=settings.access_token_expire_minutes),
        "type": "access",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Lança jwt.PyJWTError em token inválido/expirado."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
