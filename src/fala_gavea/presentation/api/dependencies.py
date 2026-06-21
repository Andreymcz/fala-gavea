from __future__ import annotations

import logging
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from fala_gavea.domain.entities.user import User
from fala_gavea.domain.exceptions import InvalidCredentialsError
from fala_gavea.domain.repositories.forwarding_repository import IForwardingRepository
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.report_type_repository import IReportTypeRepository
from fala_gavea.domain.repositories.semantic_ports import (
    ILLMClient,
    IReportIndexer,
    ISemanticSearchPort,
    ITopicModelPort,
)
from fala_gavea.domain.repositories.user_repository import IUserRepository
from fala_gavea.infrastructure.auth.jwt_service import JWTService
from fala_gavea.infrastructure.auth.password_service import PasswordService
from fala_gavea.infrastructure.database.session import SessionLocal
from fala_gavea.infrastructure.repositories.sqlalchemy_report_repository import SQLAlchemyReportRepository
from fala_gavea.infrastructure.repositories.sqlalchemy_report_type_repository import SQLAlchemyReportTypeRepository
from fala_gavea.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository

_log = logging.getLogger(__name__)
_indexer_instance: IReportIndexer | None = None
_llm_client_instance: ILLMClient | None = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_repo(db: Session = Depends(get_db)) -> IUserRepository:
    return SQLAlchemyUserRepository(db)


def get_report_repo(db: Session = Depends(get_db)) -> IReportRepository:
    return SQLAlchemyReportRepository(db)


def get_report_type_repo(db: Session = Depends(get_db)) -> IReportTypeRepository:
    return SQLAlchemyReportTypeRepository(db)


def get_password_service() -> PasswordService:
    return PasswordService()


def get_jwt_service() -> JWTService:
    return JWTService()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: IUserRepository = Depends(get_user_repo),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> User:
    try:
        payload = jwt_service.decode_token(token)
        user_id: str = payload.get("sub", "")
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = user_repo.find_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(role: str):
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return current_user
    return _check


def get_report_indexer() -> IReportIndexer | None:
    global _indexer_instance
    if _indexer_instance is None:
        try:
            from fala_gavea.infrastructure.chromadb.chroma_search_client import ChromaSearchClient
            from fala_gavea.infrastructure.embeddings.registry import SemanticConfig
            _indexer_instance = ChromaSearchClient(SemanticConfig())
        except Exception as exc:
            _log.warning("ChromaSearchClient unavailable: %s", exc)
    return _indexer_instance


def get_semantic_search_port() -> ISemanticSearchPort | None:
    # ChromaSearchClient implementa IReportIndexer e ISemanticSearchPort;
    # reaproveita o singleton de get_report_indexer (modelo carregado uma vez).
    client = get_report_indexer()
    return client  # type: ignore[return-value]


def get_topic_model_port() -> ITopicModelPort | None:
    return None


def get_keyword_extractor() -> ITopicModelPort | None:
    try:
        from fala_gavea.infrastructure.topics.tfidf_keyword_client import TfidfKeywordClient
        return TfidfKeywordClient()
    except Exception as exc:
        _log.warning("TfidfKeywordClient unavailable: %s", exc)
        return None


def get_llm_client() -> ILLMClient | None:
    global _llm_client_instance
    if _llm_client_instance is None:
        try:
            from fala_gavea.infrastructure.llm.factory import create_llm_client
            _llm_client_instance = create_llm_client()
        except Exception as exc:
            _log.warning("LLM client unavailable: %s", exc)
    return _llm_client_instance


def get_forwarding_repo(db: Session = Depends(get_db)) -> IForwardingRepository:
    from fala_gavea.infrastructure.repositories.sqlalchemy_forwarding_repository import SQLAlchemyForwardingRepository
    return SQLAlchemyForwardingRepository(db)


def require_any_role(*roles: str):
    """Returns a dependency that raises 403 if current_user.role not in roles."""
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of the following roles required: {', '.join(roles)}",
            )
        return current_user
    return _check
