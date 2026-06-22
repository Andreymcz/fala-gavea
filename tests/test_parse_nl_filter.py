import pytest
from unittest.mock import MagicMock
from fala_gavea.application.use_cases.nl.parse_nl_filter import ParseNLFilter
from fala_gavea.domain.repositories.filter_ports import IFilterParser, ParseError


class FakeParser(IFilterParser):
    def __init__(self, result):
        self._result = result

    def parse(self, text):
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


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
