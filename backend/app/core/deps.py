"""Dependencies compartilhadas: sessão de DB e usuário autenticado (seção 40)."""
from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_session
from app.models import AnalysisRun, Dataset, Project, User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login", auto_error=False
)

DbSession = Annotated[Session, Depends(get_session)]


def get_current_user(
    db: DbSession,
    header_token: Annotated[str | None, Depends(oauth2_scheme)] = None,
    query_token: Annotated[str | None, Query(alias="token")] = None,
) -> User:
    """Aceita o token via cabeçalho ``Authorization: Bearer`` OU ``?token=``
    (necessário para servir imagens/PDFs em ``<img>`` / links diretos)."""
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou expiradas.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = header_token or query_token
    if not token:
        raise cred_exc
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id or payload.get("type") != "access":
            raise cred_exc
    except jwt.PyJWTError:
        raise cred_exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise cred_exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_owned_project(project_id: str, db: DbSession, user: CurrentUser) -> Project:
    """Carrega um projeto garantindo que pertence ao usuário atual (isolamento)."""
    project = db.get(Project, project_id)
    if project is None or project.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    return project


OwnedProject = Annotated[Project, Depends(get_owned_project)]


def get_owned_dataset(dataset_id: str, db: DbSession, user: CurrentUser) -> Dataset:
    ds = db.get(Dataset, dataset_id)
    if ds is None:
        raise HTTPException(404, "Conjunto de dados não encontrado.")
    project = db.get(Project, ds.project_id)
    if project is None or project.owner_id != user.id:
        raise HTTPException(404, "Conjunto de dados não encontrado.")
    return ds


def get_owned_run(run_id: str, db: DbSession, user: CurrentUser) -> AnalysisRun:
    run = db.get(AnalysisRun, run_id)
    if run is None:
        raise HTTPException(404, "Execução não encontrada.")
    project = db.get(Project, run.project_id)
    if project is None or project.owner_id != user.id:
        raise HTTPException(404, "Execução não encontrada.")
    return run


OwnedDataset = Annotated[Dataset, Depends(get_owned_dataset)]
OwnedRun = Annotated[AnalysisRun, Depends(get_owned_run)]
