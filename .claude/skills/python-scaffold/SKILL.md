---
name: python-scaffold
description: "Scaffold a complete clean-architecture Python REST API project (FastAPI + SQLAlchemy + SQLite + Pydantic v2 + pytest) from a configurable entity name."
argument-hint: "<project-name> [--output <dir>] [--entity <EntityName>]"
compatibility: "Designed for Claude Code with the SEJA harness"
metadata:
  last-updated: 2026-06-11 02:19 UTC
  version: 1.0.0
  category: scaffolding
  context_budget: light
  references: []
---

> Overview: see [./SKILL-quickguide.md](./SKILL-quickguide.md)

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `<project-name>` | Yes | Project name in kebab-case (used as directory name and Python package base) |
| `--output <dir>` | No | Parent directory where `<project-name>/` will be created (default: current directory) |
| `--entity <EntityName>` | No | Main entity class name in PascalCase (default: `Post`) |

# Scaffold a clean Python project

Run the scaffolding script and report the output path to the user.

## Instructions

1. Parse the arguments: extract `<project-name>`, `--output` (default `.`), and `--entity` (default `Post`).

2. Run the scaffolding script:
   ```
   python .claude/skills/python-scaffold/scripts/scaffold.py \
     --name <project-name> \
     --output <output-dir> \
     --entity <EntityName>
   ```

3. Report to the user:
   - The full path of the generated project directory.
   - Quick-start instructions: `cd <project-name> && uv sync && uv run pytest -v`
   - The API entry point: `uv run uvicorn <package_name>.presentation.api.main:app --reload`

4. If the script fails, show the full error output and suggest checking that Python 3.13+ is available.
