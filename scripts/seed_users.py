"""Seed script: inserts three default dev users directly into the database.

Pre-requisites: none (creates tables if missing).

Usage:
    uv run python scripts/seed_users.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fala_gavea.domain.entities.user import User, UserRole
from fala_gavea.infrastructure.auth.password_service import PasswordService
from fala_gavea.infrastructure.database.session import SessionLocal, create_tables
from fala_gavea.infrastructure.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)

SEED_USERS = [
    ("admin@gavea.br", "admin", UserRole.admin, "admin"),
    ("citizen01@gavea.br", "citizen01", UserRole.citizen, "citizen01"),
    ("agente@gavea.br", "agente", UserRole.agent, "agente"),
]


def main() -> None:
    create_tables()
    session = SessionLocal()
    user_repo = SQLAlchemyUserRepository(session)
    password_service = PasswordService()

    created = 0
    skipped = 0
    for email, name, role, password in SEED_USERS:
        if user_repo.find_by_email(email):
            print(f"  Skipped (already exists): {email}")
            skipped += 1
        else:
            hashed = password_service.hash_password(password)
            user = User.create(email, hashed, name, role)
            user_repo.save(user)
            print(f"  Created: {email} ({role.value})")
            created += 1

    session.close()
    print(f"\nDone. Created: {created}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
