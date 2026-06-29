from fala_gavea.presentation.api.routers.nl import _to_workspace_filters


def test_collapses_plural_facets_to_singular_workspace_keys():
    body = {
        "report_type_ids": ["uuid-ilum"],
        "urgencies": ["alta"],
        "statuses": ["pendente"],
        "since": "2026-05-30",
        "until": "2026-06-29",
    }
    mapped, warnings = _to_workspace_filters(body)
    assert mapped == {
        "type_id": "uuid-ilum",
        "urgency": "alta",
        "status": "pendente",
        "since": "2026-05-30",
        "until": "2026-06-29",
    }
    assert warnings == []


def test_q_and_text_map_to_semantic_query():
    assert _to_workspace_filters({"q": "postes apagados"})[0] == {"semanticQuery": "postes apagados"}
    assert _to_workspace_filters({"text": "lixo"})[0] == {"semanticQuery": "lixo"}


def test_multi_value_facet_warns_and_keeps_first():
    mapped, warnings = _to_workspace_filters({"urgencies": ["alta", "media"]})
    assert mapped == {"urgency": "alta"}
    assert any("Urgência" in w for w in warnings)


def test_empty_body_maps_to_empty():
    assert _to_workspace_filters({}) == ({}, [])
