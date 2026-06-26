"""Pure markdown chunking, role-visibility classification, and corpus walking.

No ChromaDB or embedding dependencies live here so every function is unit-testable
in isolation. The output `DocChunk` objects are later fed to an `IDocIndexer`.
"""

from __future__ import annotations

import re
from pathlib import Path

from fala_gavea.domain.repositories.doc_ports import DocChunk

# Corpus roots scanned by default (repo-relative, forward slashes).
# Step 4 wires these into SemanticConfig; defined here as the canonical default.
_DEFAULT_ROOTS: list[str] = [
    "_output/plans",
    "_output/research-logs",
    "_output/reflections",
    "_output/communication",
    "product-design/project",
]

# Filename/path substrings that must NEVER be indexed (sensitive content).
_EXCLUDE_SUBSTRINGS: tuple[str, ...] = (
    "security-checklists",
    "threat-model",
    "secrets",
    ".env",
)

# Path fragments under _output/ that must never be indexed.
_EXCLUDE_OUTPUT_FRAGMENTS: tuple[str, ...] = (
    "_output/briefs",
    "_output/INDEX.md",
    "_output/telemetry",
    "_output/decision-digest",
    "_output/tmp/",
)

# (A3) Value-shaped secret patterns. A chunk whose text matches any of these is
# dropped. The second pattern requires a `:` or `=` followed by a 16+ char value,
# so a bare env-var NAME (e.g. "ANTHROPIC_API_KEY" with no assignment) won't match.
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(
        r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"
    ),
)

_HEADING_RE = re.compile(r"^(#{1,3})\s+(.*)$")


def classify_visibility(source_path: str) -> tuple[str, str]:
    """Return (doc_type, role_visibility) for a repo-relative path. Default-deny.

    Everything that is not explicitly public is classified `internal`.
    """
    path = source_path.replace("\\", "/")
    name = path.rsplit("/", 1)[-1]

    # --- Public surface ---
    if name == "CLAUDE.md" or name.startswith("README"):
        return ("readme", "public")

    if path.startswith("product-design/"):
        if name == "constitution.md":
            return ("constitution", "public")
        if "journey" in name:
            return ("journey", "public")
        return ("design", "public")

    if path.startswith("_output/communication/"):
        return ("communication", "public")

    # --- Internal surface (default-deny) ---
    if path.startswith("_output/plans/"):
        return ("plan", "internal")
    if path.startswith("_output/research-logs/"):
        return ("research", "internal")
    if path.startswith("_output/reflections/"):
        return ("reflection", "internal")
    if path.startswith("_output/check-logs/") or path.startswith("_output/checks/"):
        return ("check", "internal")

    return ("other", "internal")


def is_excluded(source_path: str) -> bool:
    """True for files that must NEVER be indexed (security/threat-model/secrets/etc.)."""
    path = source_path.replace("\\", "/")
    if any(token in path for token in _EXCLUDE_SUBSTRINGS):
        return True
    if any(fragment in path for fragment in _EXCLUDE_OUTPUT_FRAGMENTS):
        return True
    return False


def _contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in _SECRET_PATTERNS)


def _split_oversized(body: str, max_chars: int, overlap: int) -> list[str]:
    """Split `body` into <= max_chars pieces, each overlapping the previous by `overlap`."""
    if len(body) <= max_chars:
        return [body]
    step = max(1, max_chars - overlap)
    pieces: list[str] = []
    start = 0
    while start < len(body):
        pieces.append(body[start : start + max_chars])
        if start + max_chars >= len(body):
            break
        start += step
    return pieces


def chunk_markdown(
    text: str,
    *,
    source_path: str,
    max_chars: int = 3200,
    overlap: int = 200,
) -> list[DocChunk]:
    """Split by markdown headings (#/##/###).

    Sections larger than `max_chars` are split with `overlap`-char overlap.
    `section_title` is the nearest heading ("" if none). `chunk_index` is a
    contiguous 0-based counter across the whole document. (A3) Any sub-chunk
    whose text matches a value-shaped secret is dropped.
    """
    visibility_doc_type, role_visibility = classify_visibility(source_path)

    # Group lines into (section_title, body) segments split on headings.
    segments: list[tuple[str, list[str]]] = []
    current_title = ""
    current_lines: list[str] = []

    def flush() -> None:
        if current_lines or current_title:
            segments.append((current_title, current_lines))

    for line in text.splitlines():
        match = _HEADING_RE.match(line)
        if match:
            flush()
            current_title = match.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)
    flush()

    chunks: list[DocChunk] = []
    index = 0
    for title, body_lines in segments:
        body = "\n".join(body_lines).strip()
        if not body:
            continue
        for piece in _split_oversized(body, max_chars, overlap):
            if _contains_secret(piece):
                continue
            chunks.append(
                DocChunk(
                    chunk_id=f"{source_path}#{index}",
                    text=piece,
                    source_path=source_path,
                    doc_type=visibility_doc_type,
                    section_title=title,
                    chunk_index=index,
                    role_visibility=role_visibility,
                )
            )
            index += 1

    return chunks


def walk_corpus(roots: list[str], repo_root: str) -> list[DocChunk]:
    """Walk `roots`, skip excluded files, chunk every .md, stamp metadata.

    `source_path` is repo-relative with forward slashes. Files are read as UTF-8.
    """
    repo = Path(repo_root)
    chunks: list[DocChunk] = []
    for root in roots:
        root_dir = repo / root
        if not root_dir.exists():
            continue
        for md_file in sorted(root_dir.rglob("*.md")):
            source_path = md_file.relative_to(repo).as_posix()
            if is_excluded(source_path):
                continue
            text = md_file.read_text(encoding="utf-8")
            chunks.extend(chunk_markdown(text, source_path=source_path))
    return chunks
