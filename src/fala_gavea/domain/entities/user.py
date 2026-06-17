from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum


class UserRole(str, Enum):
    citizen = "citizen"
    agent = "agent"
    admin = "admin"


@dataclass
class User:
    id: str
    email: str
    password_hash: str
    name: str
    role: UserRole
    created_at: datetime

    @staticmethod
    def create(
        email: str,
        password_hash: str,
        name: str,
        role: UserRole = UserRole.citizen,
    ) -> User:
        return User(
            id=str(uuid.uuid4()),
            email=email,
            password_hash=password_hash,
            name=name,
            role=role,
            created_at=datetime.now(UTC),
        )
