from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.db.init_db import init_db

log = get_logger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    init_db()
    log.info("%s iniciada (env=%s)", settings.app_name, settings.app_env)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Plataforma completa de análise geoestatística: da planilha ao relatório PDF.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):  # pragma: no cover
    log.exception("Erro não tratado em %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor."})


# ---- routers -------------------------------------------------------------- #
from app.api import meta  # noqa: E402

API = settings.api_v1_prefix
app.include_router(meta.router, prefix=API)

try:  # routers adicionados na fase 3
    from app.api import datasets, exports, projects, reports, runs  # noqa: E402

    app.include_router(projects.router, prefix=API)
    app.include_router(datasets.router, prefix=API)
    app.include_router(runs.router, prefix=API)
    app.include_router(reports.router, prefix=API)
    app.include_router(exports.router, prefix=API)
except ImportError as exc:  # pragma: no cover
    log.warning("Routers de análise ainda não disponíveis: %s", exc)


@app.get("/")
def root() -> dict:
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "api": API,
    }
