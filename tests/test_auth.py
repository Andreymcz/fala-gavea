from __future__ import annotations

from fastapi.testclient import TestClient


def test_register_success(client: TestClient) -> None:
    resp = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password1", "name": "Test User"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "user@example.com"
    assert data["name"] == "Test User"
    assert data["role"] == "citizen"
    assert "id" in data
    assert "password_hash" not in data


def test_register_duplicate_email(client: TestClient) -> None:
    body = {"email": "dup@example.com", "password": "password1", "name": "User"}
    client.post("/auth/register", json=body)
    resp = client.post("/auth/register", json=body)
    assert resp.status_code == 409


def test_register_short_name(client: TestClient) -> None:
    resp = client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "password1", "name": "A"},
    )
    assert resp.status_code == 422


def test_login_success(client: TestClient) -> None:
    client.post("/auth/register", json={"email": "login@example.com", "password": "password1", "name": "Login User"})
    resp = client.post("/auth/token", data={"username": "login@example.com", "password": "password1"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient) -> None:
    client.post("/auth/register", json={"email": "wp@example.com", "password": "password1", "name": "WP User"})
    resp = client.post("/auth/token", data={"username": "wp@example.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_login_unknown_email(client: TestClient) -> None:
    resp = client.post("/auth/token", data={"username": "nobody@example.com", "password": "pass"})
    assert resp.status_code == 401


def test_me_success(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={"email": "me@example.com", "password": "password1", "name": "Me User"},
    )
    token_resp = client.post(
        "/auth/token", data={"username": "me@example.com", "password": "password1"}
    )
    token = token_resp.json()["access_token"]
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "me@example.com"
    assert data["role"] == "citizen"
    assert "id" in data
    assert "password_hash" not in data


def test_me_no_token(client: TestClient) -> None:
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_invalid_token(client: TestClient) -> None:
    resp = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401
