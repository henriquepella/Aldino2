"""Hash de senha (bcrypt).

O login foi removido da plataforma; esta função permanece apenas para
preencher a coluna ``users.hashed_password`` (não-nula) do usuário único.
"""
from __future__ import annotations

import bcrypt

_BCRYPT_MAX_BYTES = 72  # limite do algoritmo bcrypt


def hash_password(password: str) -> str:
    pw = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")
