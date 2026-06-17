import pytest

from fala_gavea.application.use_cases.create_report import (
    CreateReport,
    CreateReportInput,
)
from fala_gavea.application.use_cases.delete_report import DeleteReport
from fala_gavea.application.use_cases.get_report import GetReport
from fala_gavea.application.use_cases.list_reports import ListReports
from fala_gavea.domain.entities.report import Report
from fala_gavea.domain.exceptions import (
    ReportNotFoundError,
    InvalidInputError,
)
from fala_gavea.domain.repositories.report_repository import ReportRepository


class FakeRepository(ReportRepository):
    """In-memory fake repository for unit testing."""

    def __init__(self) -> None:
        self._store: dict[str, Report] = {}

    def save(self, entity: Report) -> Report:
        self._store[entity.id] = entity
        return entity

    def find_by_id(self, id: str) -> Report | None:
        return self._store.get(id)

    def find_all(self, limit: int = 50, offset: int = 0) -> list[Report]:
        items = list(self._store.values())
        return items[offset : offset + limit]

    def delete(self, id: str) -> bool:
        if id in self._store:
            del self._store[id]
            return True
        return False


VALID_INPUT = CreateReportInput(
    text="Precisa de mais iluminação na rua principal",
    territory_level="neighborhood",
    territory_name="Gávea",
    author_id="user-123",
)


# ── CreateReport ──────────────────────────────────────────────────────


def test_create_report_happy_path() -> None:
    repo = FakeRepository()
    entity = CreateReport(repo).execute(VALID_INPUT)
    assert entity.id is not None
    assert entity.text == VALID_INPUT.text.strip()
    assert entity.territory_level.value == "neighborhood"


def test_create_report_short_text_raises() -> None:
    repo = FakeRepository()
    with pytest.raises(InvalidInputError, match="5 characters"):
        CreateReport(repo).execute(
            CreateReportInput(
                text="Hi",
                territory_level="city",
                territory_name="Rio",
                author_id="u1",
            )
        )


def test_create_report_invalid_territory_raises() -> None:
    repo = FakeRepository()
    with pytest.raises(InvalidInputError, match="invalid territory_level"):
        CreateReport(repo).execute(
            CreateReportInput(
                text="Valid text here",
                territory_level="galaxy",
                territory_name="Milky Way",
                author_id="u1",
            )
        )


# ── GetReport ─────────────────────────────────────────────────────────


def test_get_report_found() -> None:
    repo = FakeRepository()
    created = CreateReport(repo).execute(VALID_INPUT)
    found = GetReport(repo).execute(created.id)
    assert found.id == created.id


def test_get_report_not_found_raises() -> None:
    repo = FakeRepository()
    with pytest.raises(ReportNotFoundError):
        GetReport(repo).execute("does-not-exist")


# ── ListReports ───────────────────────────────────────────────────────


def test_list_reports_empty() -> None:
    repo = FakeRepository()
    assert ListReports(repo).execute() == []


def test_list_reports_multiple() -> None:
    repo = FakeRepository()
    CreateReport(repo).execute(VALID_INPUT)
    CreateReport(repo).execute(VALID_INPUT)
    assert len(ListReports(repo).execute()) == 2


def test_list_reports_pagination() -> None:
    repo = FakeRepository()
    for _ in range(5):
        CreateReport(repo).execute(VALID_INPUT)
    page = ListReports(repo).execute(limit=2, offset=1)
    assert len(page) == 2


# ── DeleteReport ─────────────────────────────────────────────────────


def test_delete_report_found() -> None:
    repo = FakeRepository()
    created = CreateReport(repo).execute(VALID_INPUT)
    DeleteReport(repo).execute(created.id)
    assert repo.find_by_id(created.id) is None


def test_delete_report_not_found_raises() -> None:
    repo = FakeRepository()
    with pytest.raises(ReportNotFoundError):
        DeleteReport(repo).execute("ghost-id")
