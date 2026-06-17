# Research 000074 | fala-gavea | 2026-06-17 21:41 UTC | Add external data support via NL query using Overpass API
tags: overpass-api, openstreetmap, nl-query, infrastructure, architecture

## User Brief
Add external data support via NL query using the Overpass API (https://wiki.openstreetmap.org/wiki/Overpass_API).

## Agent Interpretation
Design how to integrate the Overpass API (OpenStreetMap public data query service) into fala-gavea so that agents can ask natural-language questions that retrieve OSM urban infrastructure features (streetlights, bus stops, parks, etc.) as a GeoJSON overlay on the map. This covers: (1) where the integration fits in the clean architecture, (2) how NL-to-Overpass QL translation should work, (3) which Python library/approach to use, (4) privacy and rate-limit concerns, and (5) testing strategy.

## Files Referenced
- `src/fala_gavea/infrastructure/database/models.py`
- `src/fala_gavea/presentation/api/main.py`
- `src/fala_gavea/presentation/api/routers/reports.py`
- `src/fala_gavea/config.py`
- `pyproject.toml`
- `product-design/project/constitution.md`
- `product-design/project/product-design-as-intended.md` (D-005)
- `product-design/project/standards.md` (§Backend §6)

---

## Q&A Log

### Q1: How should fala-gavea add external data support via NL query using the Overpass API?

**A:**

The Overpass API is a read-only HTTP service queried with Overpass QL (a domain-specific language with bbox, tag filters, and proximity operators). It returns JSON/GeoJSON of OSM geographic features — ideal for enriching a civic map with urban infrastructure data (streetlights, bus stops, parks, traffic signals, etc.).

#### Architecture Fit

Following constitution principle T1 and the existing OllamaClient/ChromaClient patterns, the integration requires three new components:

1. **`infrastructure/overpass/overpass_client.py`** — executes Overpass QL queries via `httpx`, returns a GeoJSON dict. Handles HTTP errors, timeouts (15s cap), and in-memory TTL cache.
2. **`application/use_cases/overpass/nl_overpass_use_case.py`** — receives NL text, calls `OllamaClient` to select a template, validates the selection, substitutes parameters, calls `OverpassClient`. This is the only layer that knows about both clients.
3. **`presentation/api/routers/overpass.py`** — new FastAPI router with `POST /overpass/features/search` (agent-only, `require_role("agent")`).

#### NL-to-QL Translation: Proposal A (template-based) is the only safe approach

Three approaches were evaluated:

| Proposal | Description | Verdict |
|----------|-------------|---------|
| A: Template-based | LLM selects 1 of 8-10 hardened QL templates, fills numeric params | **Recommended** |
| B: Raw QL generation | LLM generates Overpass QL directly | **Rejected** (injection risk, hallucination) |
| C: Predefined GET endpoints | No LLM, fixed REST params | Valid complement, not a replacement |

**Proposal B must not be implemented.** Overpass QL supports `eval()`, union operators, and recursive descent — an LLM that hallucinates a syntactically valid but semantically unbounded query could exhaust the rate limit or produce unexpected results. Proposal A constrains LLM output to an allowlist of template keys (validated before substitution) and numeric/enum parameters (range-checked before string interpolation).

**Civic templates to define (8-10)**:
- `streetlights` → `node[highway=street_lamp](bbox)`
- `bus_stops` → `node[highway=bus_stop](bbox)`
- `parks` → `way[leisure=park](bbox)`
- `potholes_road_defects` → `way[highway][surface=unpaved](bbox)`
- `traffic_signals` → `node[highway=traffic_signals](bbox)`
- `health_facilities` → `nwr[amenity~"hospital|clinic|pharmacy"](bbox)`
- `waste_collection` → `node[amenity=waste_basket](bbox)` + `node[amenity=recycling](bbox)`
- `police_fire` → `nwr[amenity~"police|fire_station"](bbox)`

#### Privacy and C1 Compliance

**The bbox question is the key design decision.** C1 states "citizen data never leaves the local machine." The Overpass API is external — it receives the query parameters including coordinates.

- **Fixed Gavea bbox** (approx. `-22.9800,-43.2500,-22.9600,-43.2100`): C1 trivially satisfied — no citizen data transmitted, only a static geographic area known from a public neighborhood boundary.
- **Dynamic coordinates** (bbox derived from a citizen-reported lat/lon): C1 is implicated — citizen-sourced coordinates would be sent to an external server. This requires an explicit D-007 decision and C1 risk acceptance.

**Default: fixed Gavea bbox only.** Dynamic coordinate queries are future work requiring an explicit design decision.

#### Python Library

Use **`httpx`** directly (already in dev deps; promote to production deps). Add `httpx` to `pyproject.toml` production dependencies. Do not add `overpy` — for `[out:json]` output, Overpass returns standard JSON parseable with `httpx.Response.json()`. Adding `overpy` would introduce a dependency for no net gain in this stack.

#### Caching and Rate Limits

The Overpass API's main instance allows ~10,000 queries/day (≈7/minute). With no caching, repeated agent page loads ("show streetlights") exhaust this quickly. **Implement an in-memory TTL cache** (10-minute expiry) inside `OverpassClient`, keyed on the QL string. A simple `dict` with `datetime` timestamps is sufficient for the PoC.

#### Timeout and Latency

Overpass API responses take 2-30 seconds depending on query complexity. The synchronous ASGI worker is blocked for this duration. For the PoC, accept this with a 15-second timeout (`httpx.timeout=15.0`) returning HTTP 504 on timeout. Document as a known PoC limitation. Cache hits return instantly and are the primary latency mitigation.

#### Endpoint Design

- **`POST /overpass/features/search`** — agent-only, body: `{ "q": "postes apagados perto da escola", "bbox": null }` (bbox optional, defaults to Gavea fixed bbox)
- Response: GeoJSON `FeatureCollection` matching the `/reports/geojson` envelope (same top-level structure, different feature properties)
- This allows Leaflet to treat the OSM overlay layer identically to the reports layer

#### Testing

Two-level mock strategy required:
1. `mock_ollama_client` — for NL-to-template-key selection
2. `mock_overpass_client` — for QL execution and response

Both must be injectable via FastAPI `Depends` (not instantiated inside the use case). Tests must cover: happy path, unrecognized NL → 422, Overpass timeout → 503/504, HTTP 429 from Overpass → 503 with Retry-After header forwarded, malformed JSON → 502.

---

## Recommendations Summary

| # | Priority | Recommendation |
|---|----------|---------------|
| 1 | HIGH | Adopt Proposal A (template-based) and explicitly reject Proposal B — LLM only selects from allowlist of 8-10 template keys, never generates raw QL |
| 2 | HIGH | Fix the Overpass bbox to the static Gavea boundary — do not forward citizen-report coordinates to the external API (C1 compliance) |
| 3 | HIGH | Add in-memory TTL cache (10-min) inside `OverpassClient` to protect the 10,000/day rate limit |
| 4 | MEDIUM | Rename endpoint to `POST /overpass/features/search`; align response envelope with `/reports/geojson` (GeoJSON FeatureCollection) |
| 5 | MEDIUM | Design two-level mock fixtures (`mock_ollama_client`, `mock_overpass_client`) before writing any test; inject both via FastAPI `Depends` |
| 6 | MEDIUM | Use `httpx` directly (promote to prod deps); do not add `overpy` |
| 7 | LOW | Document Overpass latency (2-30s), rate limit, and sync ASGI blocking as known PoC limitations in `standards.md §Backend §6` |

---

## Implementation Sketch

```
src/fala_gavea/
  infrastructure/
    overpass/
      __init__.py
      overpass_client.py        # httpx + TTL cache + 15s timeout
      templates.py              # 8-10 civic QL templates as constants
  application/
    use_cases/
      overpass/
        __init__.py
        nl_overpass_use_case.py # NL → template key (via OllamaClient) → QL → features
  presentation/
    api/
      routers/
        overpass.py             # POST /overpass/features/search (agent-only)
    schemas/
      overpass.py               # OverpassSearchRequest, OverpassFeatureCollection

tests/
  test_overpass.py              # happy path, unrecognized NL, timeout, 429, malformed JSON
```

**New dependency**: add `httpx>=0.27` to `[project.dependencies]` in `pyproject.toml` (currently only in `[project.optional-dependencies.dev]`).

**New env var**: `OVERPASS_URL` (default: `https://overpass-api.de/api/interpreter`) — allows switching to a private/no-rate-limit instance.

**Fixed Gavea bbox constant**: define as `GAVEA_BBOX = (-22.9800, -43.2500, -22.9600, -43.2100)` in `infrastructure/overpass/templates.py`.
