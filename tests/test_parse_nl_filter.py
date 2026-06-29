from datetime import datetime

import pytest
from fala_gavea.application.use_cases.nl.parse_nl_filter import ParseNLFilter
from fala_gavea.domain.entities.report_type import ReportType
from fala_gavea.domain.repositories.filter_ports import (
    FilterParseContext,
    IFilterParser,
    ParseError,
)


class FakeParser(IFilterParser):
    def __init__(self, result):
        self._result = result
        self.last_context: FilterParseContext | None = None

    def parse(self, text, context=None):
        self.last_context = context
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class FakeReportTypeRepo:
    def __init__(self, types):
        self._types = types

    def find_all_active(self):
        return self._types


def _rt(id, name):
    return ReportType(id=id, name=name, description=None, active=True, created_at=datetime(2026, 1, 1))


def test_returns_validated_body():
    parser = FakeParser({"urgencies": ["alta"], "q": "postes apagados"})
    result = ParseNLFilter(parser).execute("postes apagados urgência alta")
    assert result.body["urgencies"] == ["alta"]
    assert result.body["q"] == "postes apagados"
    assert result.warnings == []


def test_drops_unknown_keys_with_warning():
    parser = FakeParser({"q": "x", "unknown_key": "foo"})
    result = ParseNLFilter(parser).execute("x")
    assert "unknown_key" not in result.body
    assert any("ignorados" in w for w in result.warnings)


def test_none_parser_raises():
    with pytest.raises(RuntimeError):
        ParseNLFilter(None).execute("any text")


def test_parse_error_propagates():
    parser = FakeParser(ParseError(message="fail"))
    with pytest.raises(ParseError):
        ParseNLFilter(parser).execute("any")


def test_context_passed_to_parser_with_catalog_and_today():
    parser = FakeParser({})
    repo = FakeReportTypeRepo([_rt("uuid-1", "Iluminacao publica")])
    ParseNLFilter(parser, repo).execute("qualquer")
    ctx = parser.last_context
    assert ctx is not None
    assert ctx.report_types == [("uuid-1", "Iluminacao publica")]
    assert ctx.today is not None


def test_report_type_name_is_mapped_to_real_id():
    # Model returned a name/slug instead of the UUID — resolve it.
    parser = FakeParser({"report_type_ids": ["iluminação"]})
    repo = FakeReportTypeRepo([_rt("uuid-ilum", "Iluminação publica")])
    result = ParseNLFilter(parser, repo).execute("iluminação")
    assert result.body["report_type_ids"] == ["uuid-ilum"]


def test_valid_id_is_kept_and_unknown_is_dropped_with_warning():
    parser = FakeParser({"report_type_ids": ["uuid-ilum", "inexistente"]})
    repo = FakeReportTypeRepo([_rt("uuid-ilum", "Iluminação publica")])
    result = ParseNLFilter(parser, repo).execute("x")
    assert result.body["report_type_ids"] == ["uuid-ilum"]
    assert any("não reconhecidos" in w for w in result.warnings)


def test_report_type_ids_removed_when_none_resolve():
    parser = FakeParser({"report_type_ids": ["nada"], "urgencies": ["alta"]})
    repo = FakeReportTypeRepo([_rt("uuid-ilum", "Iluminação publica")])
    result = ParseNLFilter(parser, repo).execute("x")
    assert "report_type_ids" not in result.body
    assert result.body["urgencies"] == ["alta"]
