from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Generator

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

    from fala_gavea.domain.repositories.saved_filter_repository import ISavedFilterRepository

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from fala_gavea.domain.entities.user import User
from fala_gavea.domain.exceptions import InvalidCredentialsError
from fala_gavea.domain.repositories.forwarding_repository import IForwardingRepository
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.report_type_repository import IReportTypeRepository
from fala_gavea.domain.repositories.doc_ports import IDocSearchPort
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

import threading

_log = logging.getLogger(__name__)
_CHROMA_INIT_FAILED = object()
_indexer_instance: IReportIndexer | None | object = None
_indexer_lock = threading.Lock()
_llm_client_instance: ILLMClient | None = None

_embedding_model_instance: "SentenceTransformer | None" = None
_embedding_model_lock = threading.Lock()

_DOC_INIT_FAILED = object()
_doc_search_instance: IDocSearchPort | None | object = None
_doc_search_lock = threading.Lock()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


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


def get_optional_user(
    token: str | None = Depends(oauth2_scheme_optional),
    user_repo: IUserRepository = Depends(get_user_repo),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> User | None:
    if not token:
        return None
    try:
        payload = jwt_service.decode_token(token)
        user_id: str = payload.get("sub", "")
        return user_repo.find_by_id(user_id)
    except InvalidCredentialsError:
        return None


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
    if _indexer_instance is _CHROMA_INIT_FAILED:
        return None
    if _indexer_instance is not None:
        return _indexer_instance  # type: ignore[return-value]
    with _indexer_lock:
        if _indexer_instance is not None:
            return None if _indexer_instance is _CHROMA_INIT_FAILED else _indexer_instance  # type: ignore[return-value]
        try:
            from fala_gavea.infrastructure.chromadb.chroma_search_client import ChromaSearchClient
            from fala_gavea.infrastructure.embeddings.registry import SemanticConfig
            _indexer_instance = ChromaSearchClient(SemanticConfig(), model=get_embedding_model())
        except Exception as exc:
            _log.warning("ChromaSearchClient unavailable: %s", exc)
            _indexer_instance = _CHROMA_INIT_FAILED
    return None if _indexer_instance is _CHROMA_INIT_FAILED else _indexer_instance  # type: ignore[return-value]


def get_embedding_model() -> "SentenceTransformer":
    """Thread-safe lazy singleton for the shared SentenceTransformer.

    Loaded once (from SemanticConfig().embed_model_search) and reused by both the
    reports search client and the doc search client so the model is held in memory
    a single time. Import is deferred to call time to avoid the import cost at
    module load.
    """
    global _embedding_model_instance
    if _embedding_model_instance is not None:
        return _embedding_model_instance
    with _embedding_model_lock:
        if _embedding_model_instance is None:
            from sentence_transformers import SentenceTransformer

            from fala_gavea.infrastructure.embeddings.registry import SemanticConfig
            _embedding_model_instance = SentenceTransformer(SemanticConfig().embed_model_search)
    return _embedding_model_instance


def get_doc_search_port() -> IDocSearchPort | None:
    """Lazy singleton for the self-docs semantic search port.

    Mirrors get_report_indexer: returns None on init failure (sticky) so the server
    stays up in a degraded mode. Shares the single embedding model via
    get_embedding_model(), so doc search still works even if the reports Chroma
    client failed to initialize.
    """
    global _doc_search_instance
    if _doc_search_instance is _DOC_INIT_FAILED:
        return None
    if _doc_search_instance is not None:
        return _doc_search_instance  # type: ignore[return-value]
    with _doc_search_lock:
        if _doc_search_instance is not None:
            return None if _doc_search_instance is _DOC_INIT_FAILED else _doc_search_instance  # type: ignore[return-value]
        try:
            from fala_gavea.infrastructure.chromadb.chroma_doc_search_client import (
                ChromaDocSearchClient,
            )
            from fala_gavea.infrastructure.embeddings.registry import SemanticConfig
            _doc_search_instance = ChromaDocSearchClient(SemanticConfig(), get_embedding_model())
        except Exception as exc:
            _log.warning("ChromaDocSearchClient unavailable: %s", exc)
            _doc_search_instance = _DOC_INIT_FAILED
    return None if _doc_search_instance is _DOC_INIT_FAILED else _doc_search_instance  # type: ignore[return-value]


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


_filter_parser_instance = None


def get_filter_parser():
    global _filter_parser_instance
    if _filter_parser_instance is None:
        llm = get_llm_client()
        if llm is not None:
            from fala_gavea.infrastructure.llm.llm_filter_parser import LLMFilterParser
            _filter_parser_instance = LLMFilterParser(llm)
    return _filter_parser_instance


def get_anon_token_repo(db: Session = Depends(get_db)):
    from fala_gavea.infrastructure.repositories.anonymous_token_repository import SQLAlchemyAnonymousTokenRepository
    return SQLAlchemyAnonymousTokenRepository(db)


def get_forwarding_repo(db: Session = Depends(get_db)) -> IForwardingRepository:
    from fala_gavea.infrastructure.repositories.sqlalchemy_forwarding_repository import SQLAlchemyForwardingRepository
    return SQLAlchemyForwardingRepository(db)


def get_comment_repo(db: Session = Depends(get_db)):
    from fala_gavea.infrastructure.repositories.comment_repository import SQLAlchemyCommentRepository
    return SQLAlchemyCommentRepository(db)
def get_vote_repo(db: Session = Depends(get_db)):
    from fala_gavea.infrastructure.repositories.vote_repository import SQLAlchemyVoteRepository
    return SQLAlchemyVoteRepository(db)


def get_saved_filter_repo(db: Session = Depends(get_db)) -> "ISavedFilterRepository":
    from fala_gavea.infrastructure.repositories.sqlalchemy_saved_filter_repository import SQLAlchemySavedFilterRepository
    return SQLAlchemySavedFilterRepository(db)


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
