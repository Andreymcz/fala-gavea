# QA 000078 | 2026-06-17 21:47 UTC | Overpass API NL Query — Research Session

**Brief**: Research session evaluating how to add external OpenStreetMap data support via natural language queries using the Overpass API in the fala-gavea civic demand system.

---

## Q1
Add external data support via NL query using the Overpass API (https://wiki.openstreetmap.org/wiki/Overpass_API).

## A1
Ran `/research` (research-000074). Fetched Overpass API documentation and Overpass QL syntax reference. Read key project files (models, config, pyproject.toml, routers). Launched `research-reviewer` agent for multi-perspective evaluation across ARCH, SEC, DATA, API, TEST, PERF perspectives.

**Key findings and recommendations:**

1. **HIGH** — Template-based NL-to-QL (Proposal A): LLM selects from an allowlist of 8-10 hardened civic templates; never generates raw Overpass QL. Proposal B (raw QL generation) rejected due to injection/hallucination risk.
2. **HIGH** — Fixed Gavea bbox only: citizen-report coordinates must not be forwarded to the external Overpass server (C1 compliance). Dynamic coordinates require a separate D-007 decision entry.
3. **HIGH** — In-memory TTL cache (10 min) inside `OverpassClient` to protect the 10,000 queries/day rate limit.
4. **MEDIUM** — Endpoint: `POST /overpass/features/search` (agent-only); response: GeoJSON FeatureCollection matching `/reports/geojson` envelope.
5. **MEDIUM** — Two-level mock fixtures (`mock_ollama_client` + `mock_overpass_client`) injected via FastAPI `Depends` before writing tests.
6. **MEDIUM** — Use `httpx` directly (promote to prod deps); do not add `overpy`.
7. **LOW** — Document latency (2-30s), rate limit, and synchronous ASGI blocking as known PoC limitations in `standards.md §Backend §6`.

**Architecture**: 3 new components — `infrastructure/overpass/overpass_client.py` + `templates.py`, `application/use_cases/overpass/nl_overpass_use_case.py`, `presentation/api/routers/overpass.py`.

Saved report to `_output/research-logs/research-000074-overpass-api-nl-query.md`. Committed.

---

## Q2
Quais são as possíveis camadas e dados oferecidos pela Overpass API? No contexto do projeto, por exemplo, posso digitar no chat: "mostra os postes de iluminação no bbox selecionado."

## A2
Explained OSM data layers available via Overpass relevant to fala-gavea's Gávea context:

**Iluminação e infraestrutura viária**: postes (`highway=street_lamp`), semáforos (`highway=traffic_signals`), lombadas (`highway=speed_bump`), ruas não pavimentadas (`surface=unpaved`).

**Transporte público**: paradas de ônibus (`highway=bus_stop`), abrigos (`amenity=shelter`), linhas (`route=bus`).

**Áreas verdes**: parques (`leisure=park`), praças (`leisure=square`), quadras (`leisure=pitch`).

**Segurança/emergência**: delegacias (`amenity=police`), bombeiros (`amenity=fire_station`), hospitais/UPAs (`amenity=hospital|clinic`).

**Gestão de resíduos**: lixeiras (`amenity=waste_basket`), reciclagem (`amenity=recycling`), contêineres (`amenity=waste_disposal`).

**NL → template examples:**
- "mostra os postes no bbox" → `node[highway=street_lamp](bbox)` → GeoJSON layer roxo no Leaflet
- "paradas de ônibus aqui" → `node[highway=bus_stop](bbox)`
- "delegacias e bombeiros" → `nwr[amenity~"police|fire_station"](bbox)`

**Limitações**: dados OSM podem estar desatualizados; não refletem estado operacional (poste cadastrado ≠ poste funcionando); sem dados municipais internos de contratos/manutenção.

**Valor do cruzamento**: agente seleciona área com demandas de iluminação → solicita postes OSM no bbox → cruzamento visual identifica candidatos prioritários para encaminhamento.
