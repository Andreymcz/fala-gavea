# QA Log — plan-000183 | Local showcase seed pipeline + feature seeds

source: plan-000183

## Brief

create local pipeline for seeding app. create makefile entry receiving url as parameter and create a intial seed of the appplication to showcase features. There is some features that do not have any seed, like upvotes. check recent reflection to see what whas implemented and give suggestions of new seed pipeline entryes

## Q&A

**Q1:** Which new seed entries should the plan add (votes is a given)?

**A1:** User selected **all four**: Votes (upvotes/downvotes), Comments on forwardings, Saved filters, and Resolved-status + extra citizens.

**Q2:** How should the "initial showcase seed" be structured?

**A2:** **Dedicated small curated profile** — `make seed URL=...` runs a curated ~50-relato showcase (200-row CSV subset) + all feature seeds, fast and deterministic. (Alternative — wiring the full 5k seed into make — was offered but not chosen; retained as `--profile full`.)

## Findings surfaced during planning

- **`ReportStatus.resolvido` is vestigial**: the enum value exists (`report.py:19`, DB `models.py:54`, LLM filter parser) but no API path transitions a report to it. `create_forwarding` sets `encaminhado`; `update_forwarding_status` mutates only the forwarding. The app's real "resolved" concept is the **forwarding** reaching `finalizado` (`PATCH /forwardings/{id}/status`). The lifecycle seed (Step 5) advances forwardings, not reports. Marking reports `resolvido` would need a new endpoint or a DB write (violating the API-only seed convention) — noted under Suggestions.
- **Vote rate limit `20/minute` per user** (`votes.py`) and **self-vote 409 guard** (`SelfVoteError`) drove the votes-seed design: distinct voter pool (non-authors), 409 skip, 429 exponential backoff.

## Decisões / Resultado

- Plano `plan-000183` gerado (7 steps, Review: light) — tooling-only, API-driven seeds.
- 4 new scripts (votes, comments, saved-filters, forwarding-lifecycle) + extra citizen accounts + `seed_all.py --profile {showcase,full}` + `make seed URL=...` target + docs.
- Suggestions section lists 5 future seed entries (anonymous reports/claim tokens, AI report-type provenance after plan-000174, `em_analise` reports, a true report-level `resolvido` path, self-docs reindex convenience).
