from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from fala_gavea.infrastructure.database.session import create_tables
from fala_gavea.presentation.api.routers import auth as auth_router
from fala_gavea.presentation.api.routers import report_types as report_types_router
from fala_gavea.presentation.api.routers import reports as reports_router
from fala_gavea.presentation.api.routers import forwardings as forwardings_router

STATIC_DIR = Path(__file__).resolve().parents[4] / "static"


def _mount_spa(app: FastAPI) -> None:
    if not STATIC_DIR.exists():
        return
    assets = STATIC_DIR / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str) -> FileResponse:
        candidate = STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")


def create_app() -> FastAPI:
    app = FastAPI(title="Fala Gavea API", version="0.1.0")
    create_tables()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(reports_router.router, prefix="/reports", tags=["reports"])
    app.include_router(report_types_router.router, prefix="/report_types", tags=["report_types"])
    app.include_router(forwardings_router.router, prefix="/forwardings", tags=["forwardings"])
    _mount_spa(app)
    return app


app = create_app()
