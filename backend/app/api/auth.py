from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.deps import CurrentUser, DbSession
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.auth import RegisterRequest, Token, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=201)
def register(payload: RegisterRequest, db: DbSession) -> Token:
    if not settings.allow_registration:
        raise HTTPException(403, "Cadastro desabilitado neste ambiente.")
    exists = db.query(User).filter(User.email == payload.email.lower()).first()
    if exists:
        raise HTTPException(409, "E-mail já cadastrado.")
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue(user)


@router.post("/login", response_model=Token)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> Token:
    user = db.query(User).filter(User.email == form.username.lower()).first()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(403, "Conta inativa.")
    return _issue(user)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> User:
    return user


def _issue(user: User) -> Token:
    token = create_access_token(user.id, extra={"email": user.email})
    return Token(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
    )
