from __future__ import annotations

from fastapi.testclient import TestClient


def test_api_works_without_static_dir(client: TestClient) -> None:
    """When STATIC_DIR does not exist the API endpoints are fully functional."""
    # Public endpoint still responds
    resp = client.get("/report_types")
    assert resp.status_code == 200


def test_auth_me_still_requires_token_without_static_dir(client: TestClient) -> None:
    """SPA fallback must not shadow protected API routes -- /auth/me requires auth."""
    resp = client.get("/auth/me")
    assert resp.status_code == 401
