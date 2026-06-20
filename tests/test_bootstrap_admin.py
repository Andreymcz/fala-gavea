"""Tests for BootstrapAdminUser use case."""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from fala_gavea.application.use_cases.admin.bootstrap_admin_user import BootstrapAdminUser
from fala_gavea.infrastructure.auth.password_service import PasswordService
from fala_gavea.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository


def test_bootstrap_creates_admin_user(db_session, monkeypatch) -> None:
    monkeypatch.setenv("FALA_GAVEA_ADMIN_EMAIL", "admin@boot.com")
    monkeypatch.setenv("FALA_GAVEA_ADMIN_PASSWORD", "securepass")
    monkeypatch.setenv("FALA_GAVEA_ADMIN_NAME", "Boot Admin")

    repo = SQLAlchemyUserRepository(db_session)
    ps = PasswordService()
    BootstrapAdminUser().execute(repo, ps)

    user = repo.find_by_email("admin@boot.com")
    assert user is not None
    assert user.name == "Boot Admin"
    assert user.role.value == "admin"


def test_bootstrap_no_duplicate(db_session, monkeypatch) -> None:
    monkeypatch.setenv("FALA_GAVEA_ADMIN_EMAIL", "admin@boot.com")
    monkeypatch.setenv("FALA_GAVEA_ADMIN_PASSWORD", "securepass")

    repo = SQLAlchemyUserRepository(db_session)
    ps = PasswordService()
    BootstrapAdminUser().execute(repo, ps)
    BootstrapAdminUser().execute(repo, ps)  # second run should be no-op

    from sqlalchemy import text
    count = db_session.execute(
        text("SELECT COUNT(*) FROM users WHERE email='admin@boot.com'")
    ).scalar()
    assert count == 1


def test_bootstrap_skipped_when_env_absent(db_session, monkeypatch) -> None:
    monkeypatch.delenv("FALA_GAVEA_ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("FALA_GAVEA_ADMIN_PASSWORD", raising=False)

    repo = SQLAlchemyUserRepository(db_session)
    ps = PasswordService()
    BootstrapAdminUser().execute(repo, ps)

    from sqlalchemy import text
    count = db_session.execute(text("SELECT COUNT(*) FROM users")).scalar()
    assert count == 0


def test_bootstrap_admin_can_authenticate(client: TestClient, db_session, monkeypatch) -> None:
    monkeypatch.setenv("FALA_GAVEA_ADMIN_EMAIL", "admin@boot.com")
    monkeypatch.setenv("FALA_GAVEA_ADMIN_PASSWORD", "securepass")

    repo = SQLAlchemyUserRepository(db_session)
    ps = PasswordService()
    BootstrapAdminUser().execute(repo, ps)
    db_session.commit()

    resp = client.post("/auth/token", data={"username": "admin@boot.com", "password": "securepass"})
    assert resp.status_code == 200
    payload = resp.json()
    assert "access_token" in payload
