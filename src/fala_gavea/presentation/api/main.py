from __future__ import annotations

import logging
import os
from pathlib import Path

# Allow fine-grained log level control via env var, e.g.:
#   FALA_GAVEA_LOG_LEVEL=DEBUG uv run uvicorn ...
_log_level = os.environ.get("FALA_GAVEA_LOG_LEVEL", "INFO").upper()
_fala_logger = logging.getLogger("fala_gavea")
_fala_logger.setLevel(_log_level)
if _log_level == "DEBUG" and not _fala_logger.handlers:
    _dbg_handler = logging.StreamHandler()
    _dbg_handler.setLevel(logging.DEBUG)
    _dbg_handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    _fala_logger.addHandler(_dbg_handler)

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text
from fastapi.staticfiles import StaticFiles

from fala_gavea.application.use_cases.admin.bootstrap_admin_user import BootstrapAdminUser
from fala_gavea.infrastructure.auth.password_service import PasswordService
from fala_gavea.infrastructure.database.session import SessionLocal, create_tables
from fala_gavea.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from fala_gavea.presentation.api.routers import auth as auth_router
from fala_gavea.presentation.api.routers import nl as nl_router
from fala_gavea.presentation.api.routers import report_types as report_types_router
from fala_gavea.presentation.api.routers import reports as reports_router
from fala_gavea.presentation.api.routers import forwardings as forwardings_router
from fala_gavea.presentation.api.routers import seed as seed_router
from fala_gavea.presentation.api.routers import saved_filters as saved_filters_router
from fala_gavea.presentation.api.routers import comments as comments_router
from fala_gavea.presentation.api.routers.votes import forwardings_votes_router, reports_votes_router

STATIC_DIR = Path(__file__).resolve().parents[4] / "static"

_API_PREFIXES = {
    "auth", "reports", "report_types", "forwardings",
    "nl", "admin", "health", "docs", "saved-filters",
}


def _mount_spa(app: FastAPI) -> None:
    if not STATIC_DIR.exists():
        return
    assets = STATIC_DIR / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")
    docs = STATIC_DIR / "docs"
    if docs.exists():
        app.mount("/docs", StaticFiles(directory=docs, html=True), name="docs")

    @app.get("/{full_path:path}", include_in_schema=False, response_model=None)
    def spa_fallback(full_path: str) -> FileResponse | JSONResponse:
        first_segment = full_path.split("/")[0] if full_path else ""
        if first_segment in _API_PREFIXES:
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        candidate = STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")


def create_app() -> FastAPI:
    app = FastAPI(title="Fala Gavea API", version="0.1.0")
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    create_tables()

    db = SessionLocal()
    try:
        BootstrapAdminUser().execute(SQLAlchemyUserRepository(db), PasswordService())
    finally:
        db.close()

    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(nl_router.router, prefix="/nl", tags=["nl"])
    app.include_router(reports_router.router, prefix="/reports", tags=["reports"])
    app.include_router(report_types_router.router, prefix="/report_types", tags=["report_types"])
    app.include_router(forwardings_router.router, prefix="/forwardings", tags=["forwardings"])
    app.include_router(seed_router.router, prefix="/admin/seed", tags=["seed"])
    app.include_router(saved_filters_router.router, prefix="/saved-filters", tags=["saved-filters"])
    app.include_router(
        comments_router.router,
        prefix="/forwardings/{forwarding_id}/comments",
        tags=["comments"],
    )
    app.include_router(reports_votes_router, prefix="/reports", tags=["votes"])
    app.include_router(forwardings_votes_router, prefix="/forwardings", tags=["votes"])

    @app.get("/health", include_in_schema=False)
    def health() -> JSONResponse:
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
        except Exception:
            return JSONResponse({"status": "error", "detail": "db unavailable"}, status_code=503)
        return JSONResponse({"status": "ok"})

    _mount_spa(app)
    return app


app = create_app()
