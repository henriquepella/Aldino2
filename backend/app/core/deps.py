"""Dependencies compartilhadas: sessão de DB e usuário da aplicação.

O sistema de login foi removido — a plataforma opera com um único usuário
implícito (o "usuário demo"), criado automaticamente no primeiro acesso.
Todas as rotas continuam recebendo um ``User`` real, de modo que os vínculos
por ``owner_id`` e o isolamento de arquivos em disco seguem funcionando.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.init_db import ensure_demo_user
from app.db.session import get_session
from app.models import AnalysisRun, Dataset, Project, User

DbSession = Annotated[Session, Depends(get_session)]


def get_current_user(db: DbSession) -> User:
    """Retorna o usuário único da aplicação (criado sob demanda)."""
    return ensure_demo_user(db)


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
