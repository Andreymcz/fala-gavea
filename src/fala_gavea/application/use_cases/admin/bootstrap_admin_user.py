from __future__ import annotations

import logging
import os
import uuid
from datetime import UTC, datetime

from fala_gavea.domain.entities.user import User, UserRole
from fala_gavea.domain.repositories.user_repository import IUserRepository
from fala_gavea.infrastructure.auth.password_service import PasswordService

_log = logging.getLogger(__name__)


class BootstrapAdminUser:
    def execute(self, user_repo: IUserRepository, password_service: PasswordService) -> None:
        email = os.environ.get("FALA_GAVEA_ADMIN_EMAIL", "").strip()
        password = os.environ.get("FALA_GAVEA_ADMIN_PASSWORD", "").strip()
        name = os.environ.get("FALA_GAVEA_ADMIN_NAME", "Admin").strip() or "Admin"

        if not email or not password:
            _log.debug("Bootstrap admin skipped: env vars not set")
            return

        if user_repo.find_by_email(email) is not None:
            _log.debug("Bootstrap admin skipped: user %s already exists", email)
            return

        hashed = password_service.hash_password(password)
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            password_hash=hashed,
            name=name,
            role=UserRole.admin,
            created_at=datetime.now(UTC),
        )
        user_repo.save(user)
        _log.info("Bootstrap admin user created: %s", email)
