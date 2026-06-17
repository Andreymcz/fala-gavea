from __future__ import annotations

from fastapi import FastAPI

from fala_gavea.infrastructure.database.session import create_tables
from fala_gavea.presentation.api.routers import auth as auth_router
from fala_gavea.presentation.api.routers import reports as reports_router


def create_app() -> FastAPI:
    app = FastAPI(title="Fala Gavea API", version="0.1.0")
    create_tables()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(reports_router.router, prefix="/reports", tags=["reports"])
    return app


app = create_app()
