from __future__ import annotations

from pathlib import Path

from fala_gavea.infrastructure.docs.markdown_chunker import (
    _DEFAULT_ROOTS,
    chunk_markdown,
    classify_visibility,
    is_excluded,
    walk_corpus,
)


# --- (a) classify_visibility ---------------------------------------------


def test_classify_plan_path_is_internal() -> None:
    assert classify_visibility("_output/plans/plan-000174-foo.md") == ("plan", "internal")


def test_classify_communication_path_is_public() -> None:
    assert classify_visibility("_output/communication/letter.md") == (
        "communication",
        "public",
    )


def test_classify_constitution_is_public_constitution() -> None:
    assert classify_visibility("product-design/project/constitution.md") == (
        "constitution",
        "public",
    )


def test_classify_journey_file_is_journey() -> None:
    doc_type, visibility = classify_visibility("product-design/project/citizen-journey.md")
    assert doc_type == "journey"
    assert visibility == "public"


def test_classify_ux_research_stays_design() -> None:
    doc_type, visibility = classify_visibility("product-design/project/ux-research-results.md")
    assert doc_type == "design"
    assert visibility == "public"


def test_classify_readme_is_public_readme() -> None:
    assert classify_visibility("README.md") == ("readme", "public")


def test_classify_claude_md_is_public_readme() -> None:
    assert classify_visibility("CLAUDE.md") == ("readme", "public")


def test_classify_research_log_is_internal() -> None:
    assert classify_visibility("_output/research-logs/r-000170.md") == (
        "research",
        "internal",
    )


def test_classify_reflection_is_internal() -> None:
    assert classify_visibility("_output/reflections/refl-000173.md") == (
        "reflection",
        "internal",
    )


def test_classify_check_log_is_internal() -> None:
    assert classify_visibility("_output/check-logs/c-1.md") == ("check", "internal")


def test_classify_unknown_defaults_to_other_internal() -> None:
    assert classify_visibility("scripts/seed_all.py") == ("other", "internal")


# --- (b) is_excluded ------------------------------------------------------


def test_is_excluded_security_checklists() -> None:
    assert is_excluded("product-design/project/security-checklists.md") is True


def test_is_excluded_tmp_dir() -> None:
    assert is_excluded("_output/tmp/x.md") is True


def test_is_excluded_threat_model() -> None:
    assert is_excluded("product-design/threat-model.md") is True


def test_is_excluded_index() -> None:
    assert is_excluded("_output/INDEX.md") is True


def test_is_excluded_normal_plan_is_false() -> None:
    assert is_excluded("_output/plans/plan-000174-foo.md") is False


# --- (c) chunk_markdown: headings -> chunks -------------------------------


def test_chunk_three_headings_yields_three_chunks() -> None:
    text = (
        "# First\n"
        "Body of first section.\n\n"
        "## Second\n"
        "Body of second section.\n\n"
        "### Third\n"
        "Body of third section.\n"
    )
    chunks = chunk_markdown(text, source_path="_output/plans/p.md")
    assert len(chunks) == 3
    assert [c.section_title for c in chunks] == ["First", "Second", "Third"]
    assert [c.chunk_index for c in chunks] == [0, 1, 2]
    assert chunks[0].chunk_id == "_output/plans/p.md#0"
    assert all(c.source_path == "_output/plans/p.md" for c in chunks)


# --- (d) oversized section splits with overlap ----------------------------


def test_oversized_section_splits_with_overlap() -> None:
    body = "x" * 5000
    text = f"# Big\n{body}\n"
    chunks = chunk_markdown(text, source_path="_output/plans/big.md", max_chars=1000, overlap=100)
    assert len(chunks) > 1
    assert all(len(c.text) <= 1000 for c in chunks)
    assert all(c.section_title == "Big" for c in chunks)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    # overlap: end of one sub-chunk reappears at start of the next
    tail = chunks[0].text[-100:]
    assert tail in chunks[1].text


# --- (e) (A3) secret-pattern content guard --------------------------------


def test_value_shaped_secret_chunk_is_dropped() -> None:
    text = "# Leak\nsk-ABCDEFGHIJKLMNOPQRSTUV is a key\n"
    chunks = chunk_markdown(text, source_path="_output/plans/leak.md")
    assert chunks == []


def test_assigned_api_key_value_is_dropped() -> None:
    text = '# Cfg\napi_key = "abcdef0123456789ABCDEF"\n'
    chunks = chunk_markdown(text, source_path="_output/plans/cfg.md")
    assert chunks == []


def test_bare_env_var_name_is_retained() -> None:
    text = "# Env\nSet ANTHROPIC_API_KEY and FALA_GAVEA_OLLAMA_URL in your shell.\n"
    chunks = chunk_markdown(text, source_path="_output/plans/env.md")
    assert len(chunks) == 1
    assert "ANTHROPIC_API_KEY" in chunks[0].text


# --- walk_corpus ----------------------------------------------------------


def test_default_roots_constant() -> None:
    assert _DEFAULT_ROOTS == [
        "_output/plans",
        "_output/research-logs",
        "_output/reflections",
        "_output/communication",
        "product-design/project",
    ]


def test_walk_corpus_reads_chunks_and_stamps_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path
    plans = repo_root / "_output" / "plans"
    plans.mkdir(parents=True)
    (plans / "plan-1.md").write_text("# Heading\nSome body text.\n", encoding="utf-8")
    # excluded file must not appear
    tmp = repo_root / "_output" / "tmp"
    tmp.mkdir(parents=True)
    (tmp / "scratch.md").write_text("# Skip\nbody\n", encoding="utf-8")

    chunks = walk_corpus(["_output/plans", "_output/tmp"], str(repo_root))
    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.source_path == "_output/plans/plan-1.md"
    assert chunk.doc_type == "plan"
    assert chunk.role_visibility == "internal"
    assert chunk.section_title == "Heading"
    assert chunk.chunk_index == 0
