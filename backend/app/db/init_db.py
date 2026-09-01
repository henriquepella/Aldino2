"""Criação de tabelas e seed do usuário demo."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import User

log = get_logger("db.init")


def create_all() -> None:
    import app.models  # noqa: F401  (garante registro de todos os modelos)

    Base.metadata.create_all(bind=engine)
    log.info("Tabelas verificadas/criadas em %s", settings.database_url)


def ensure_demo_user(db: Session) -> User:
    user = db.query(User).filter(User.email == settings.demo_email).one_or_none()
    if user is None:
        user = User(
            email=settings.demo_email,
            full_name=settings.demo_full_name,
            hashed_password=hash_password(settings.demo_password),
            is_active=True,
            is_demo=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        log.info("Usuário demo criado: %s", settings.demo_email)
    return user


def init_db() -> None:
    create_all()
    with SessionLocal() as db:
        ensure_demo_user(db)


if __name__ == "__main__":  # pragma: no cover
    init_db()
