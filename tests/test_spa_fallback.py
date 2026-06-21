"""Regression tests for SPA catch-all guard."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def test_report_types_trailing_slash_returns_json(client: TestClient) -> None:
    """GET /report_types/ (with trailing slash) returns JSON, not HTML."""
    resp = client.get("/report_types/")
    assert resp.status_code == 200
    assert "application/json" in resp.headers.get("content-type", "")
    assert "text/html" not in resp.headers.get("content-type", "")


def test_forwardings_trailing_slash_returns_json(client: TestClient, agent_headers: dict) -> None:
    """GET /forwardings/ returns JSON for authenticated agent."""
    resp = client.get("/forwardings/", headers=agent_headers)
    assert resp.status_code == 200
    assert "application/json" in resp.headers.get("content-type", "")


def test_auth_me_still_requires_token(client: TestClient) -> None:
    """Auth endpoints return JSON errors (not SPA HTML) when unauthenticated."""
    resp = client.get("/auth/me")
    assert resp.status_code == 401
    assert "application/json" in resp.headers.get("content-type", "")


def test_reports_geojson_returns_json(client: TestClient) -> None:
    """GET /reports/geojson returns JSON (public endpoint)."""
    resp = client.get("/reports/geojson")
    assert resp.status_code == 200
    assert "application/json" in resp.headers.get("content-type", "")


def test_spa_guard_blocks_api_prefix_when_static_exists(tmp_path: Path) -> None:
    """When STATIC_DIR exists, API-prefixed paths are blocked with 404 JSON by guard."""
    # Create a minimal STATIC_DIR with index.html so _mount_spa installs the guard
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<html>SPA</html>")

    import fala_gavea.presentation.api.main as main_mod

    original = main_mod.STATIC_DIR
    try:
        main_mod.STATIC_DIR = static_dir

        import os
        os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing")
        os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

        app = main_mod.create_app()
        with TestClient(app, raise_server_exceptions=False) as c:
            # Known API prefix: guard should return 404 JSON, not SPA HTML
            resp = c.get("/report_types/nonexistent-route")
            assert resp.status_code == 404
            assert "application/json" in resp.headers.get("content-type", "")
            data = resp.json()
            assert "detail" in data

            # Unknown path: should serve SPA index.html
            resp = c.get("/some/unknown/spa-path")
            assert resp.status_code == 200
            assert "text/html" in resp.headers.get("content-type", "")
    finally:
        main_mod.STATIC_DIR = original


def test_spa_guard_api_prefix_list_is_comprehensive() -> None:
    """Verify _API_PREFIXES contains all mounted router prefixes."""
    from fala_gavea.presentation.api.main import _API_PREFIXES

    expected = {"auth", "reports", "report_types", "forwardings", "nl", "admin", "health", "docs"}
    assert expected <= _API_PREFIXES
