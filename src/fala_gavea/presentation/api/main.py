from __future__ import annotations

from fastapi import FastAPI

from fala_gavea.infrastructure.database.session import create_tables
from fala_gavea.presentation.api.routers import auth as auth_router
from fala_gavea.presentation.api.routers import report_types as report_types_router
from fala_gavea.presentation.api.routers import reports as reports_router
from fala_gavea.presentation.api.routers import forwardings as forwardings_router


def create_app() -> FastAPI:
    app = FastAPI(title="Fala Gavea API", version="0.1.0")
    create_tables()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(reports_router.router, prefix="/reports", tags=["reports"])
    app.include_router(report_types_router.router, prefix="/report_types", tags=["report_types"])
    app.include_router(forwardings_router.router, prefix="/forwardings", tags=["forwardings"])
    return app


app = create_app()
