# Communication 000128 | ACD | 2026-06-21 15:31 UTC | Academics

**Project:** fala-gavea  
**Audience:** Academics -- course professors and researchers (INF2921/CIS2114, AI Systems Design 2026.1)  
**Team:** Andrey, Mauro, Julia, Herbert, Natali  
**Date:** 2026-06-21

---

## Abstract

fala-gavea is a citizen-facing urban safety demand system for the Gavea district, built as a research artifact for the AI Systems Design course. Citizens register problems (location, type, urgency); public agents create institutional forwardings; AI components assist agent sensemaking via semantic search, topic modeling, and a RAG-backed natural-language assistant. The system is designed as an explicit instantiation of semiotic engineering principles -- the interface and its AI layer are understood as a designer-to-user metacommunication channel, not merely as functional software.

---

## 1. Theoretical Foundation

### 1.1 Semiotic Engineering Framing

The design treats the interface as a message from the design team to users, following Prates and Barbosa's metacommunication framework. Each interaction surface encodes a designer intent: "here is who you are, what you can do, and why."

Three concrete design decisions operationalize this:

1. **Role encoding as metacommunication.** The system defines three user roles -- citizen, agent, admin -- each with distinct permissions and distinct views. The role assignment is not merely an access-control mechanism; it is the designer's statement about the social contract of urban safety management. A citizen can register and track. An agent can act. The asymmetry is intentional and visible.

2. **Multi-perspective workspace as epistemic stance.** The agent workspace presents five views over the same corpus of reports: map, table, topic keywords, semantic similarity, and NL chat. This is a deliberate metacommunication: "there is no single correct reading of citizen demands; here are five lenses." The AI-powered views (topics, similarity, chat) are presented alongside the non-AI views (map, table), encoding the position that AI is one lens among several, not an authority.

3. **Cited sources as hallucination transparency.** The RAG assistant returns `cited_report_ids` alongside every response. In the frontend, these IDs render as focusable buttons that trigger the semantic similarity view for the cited report. This design decision makes the AI's evidential basis navigable and auditable by the human agent, addressing the opacity problem of generative AI in decision-support contexts.

### 1.2 AI-Assisted Development as Research Practice

The project was developed using Claude Code (Anthropic) as a primary development assistant, operating within a structured skill lifecycle: `/research` > `/plan` > `/implement` > `/check`. This process generates a corpus of plan artifacts (`_output/plans/`) and research briefs (`_output/briefs.md`) that document design decisions and rationale as they were made. The development process itself is thus partially reproducible: the artifact trail shows not only what was built but what was considered and deferred.

This positions AI-assisted development not merely as a productivity tool but as a design documentation practice -- the AI interlocutor forces explicit articulation of intent that would otherwise remain tacit.

---

## 2. System Architecture as Research Artifact

### 2.1 Clean Architecture and the Port/Adapter Pattern

The system follows a strict four-layer architecture:

```
domain/          -- pure dataclasses and repository ABCs; zero I/O dependencies
application/     -- use cases; orchestrate domain objects; no direct DB or HTTP
infrastructure/  -- concrete implementations: SQLAlchemy, ChromaDB, Ollama, Anthropic
presentation/    -- FastAPI routers, Pydantic schemas, JWT auth
```

The architecture enforces a dependency rule: inner layers never import outer layers. This has a specific research implication: every AI component is represented as an abstract port (interface) at the domain/application boundary, with concrete infrastructure implementations that can be substituted independently.

Key ports:

| Port (ABC) | Infrastructure implementations |
|---|---|
| `IReportIndexer` | `ChromaReportIndexer` |
| `ISemanticSearchPort` | `ChromaSemanticSearch` |
| `ITopicModelPort` | `BERTopicClient`, `TfidfTopicsClient` |
| `ILLMClient` | `OllamaClient`, `AnthropicClient` |

This means AI components are substitutable without touching use cases or routers -- a property relevant for controlled experiments comparing provider behavior.

### 2.2 LLM Provider Abstraction

`infrastructure/llm/factory.py` dispatches between Ollama (local, default `qwen3:8b`) and the Anthropic API based on an environment variable. This makes the privacy/capability trade-off explicit and configurable at deployment time:

- **Ollama (local):** data never leaves the server; suitable for sensitive civic data; lower capability ceiling
- **Anthropic API:** higher capability; data leaves the local environment; requires explicit opt-in via env var

The abstraction is not merely technical convenience -- it encodes a design position that the choice of LLM provider is a governance decision, not a configuration detail.

### 2.3 Graceful Degradation

ChromaDB and Ollama unavailability return HTTP 503 (service unavailable), not 500 (server error). The system continues serving non-AI features (citizen registration, agent forwarding, map view, table view) when AI infrastructure is down. This degrades gracefully across the capability spectrum: the system remains useful even when its most sophisticated features are unavailable.

From a research perspective, this architecture allows studying the system at multiple capability levels -- with and without each AI component -- without code changes.

### 2.4 Embedding Registry

`infrastructure/embeddings/registry.py` manages sentence-transformer model loading. The current default is `intfloat/multilingual-e5-small`, chosen for the memory constraints of Railway (cloud PaaS) deployment while maintaining Portuguese-language embedding quality. The registry is a substitution point for comparative embedding experiments.

---

## 3. AI Integration Points

### 3.1 Semantic Search (ChromaDB + sentence-transformers)

Reports are indexed into ChromaDB at creation time via `IReportIndexer`. Agents query the index via `ISemanticSearchPort`, which returns thematically similar reports regardless of lexical overlap. This enables discovery of latent clusters -- e.g., reports about "broken streetlight on Rua Marques" and "dark alley near the PUC gate" share semantic proximity without sharing keywords.

The embedding model operates over the concatenation of report description and location, treating spatial and semantic proximity as jointly informative.

### 3.2 Topic Modeling (BERTopic / TF-IDF)

`ITopicModelPort` surfaces latent themes in the report corpus. Two implementations exist:

- **BERTopicClient:** neural topic modeling; higher quality; higher memory cost
- **TfidfTopicsClient:** lightweight TF-IDF keyword extraction; low memory; currently wired as the default for Railway deployment

The dual implementation is a concrete example of the capability/cost trade-off that characterizes real-world AI system design -- and a substitution the architecture makes transparent.

### 3.3 RAG NL Assistant

The NL chat assistant (agent workspace, "Chat" view) implements a retrieval-augmented generation pattern:

1. Agent submits a natural-language query in Portuguese (e.g., "quais sao as principais reclamacoes sobre iluminacao?")
2. The query is embedded and used to retrieve the top-5 semantically similar reports from ChromaDB
3. A pt-BR system prompt is constructed with the retrieved report excerpts as context
4. The LLM generates a response grounded in the retrieved context
5. The response includes `cited_report_ids` -- the IDs of the reports used as context

Step 5 is the critical design decision: the cited IDs are returned to the frontend as structured data, not embedded in prose. This allows the UI to render them as interactive elements that link to the semantic similarity view -- closing a loop where AI-generated insight feeds back into human-directed investigation.

---

## 4. Metacommunication Design Analysis

### 4.1 The Workspace as Sign System

The agent workspace can be analyzed as a sign system in the semiotic engineering sense. Each view is a sign vehicle:

- **Map view:** iconic sign -- spatial representation of report locations; invites geographic sensemaking
- **Table view:** symbolic/indexical -- structured listing; invites sorting and filtering
- **Topics view:** symbolic -- keyword clusters; invites thematic categorization
- **Similar view:** indexical -- "reports like this one"; invites analogical reasoning
- **Chat view:** symbolic -- NL dialogue; invites interrogative sensemaking

The five views together constitute a metalinguistic statement: "citizen demands are complex objects; no single representation suffices." The designer's intent is that agents develop a richer model of the demand corpus by moving across views, not by trusting any single one.

### 4.2 The AI as Interlocutor, Not Oracle

A deliberate design decision was to frame the AI assistant as a conversational interlocutor rather than a decision system. The chat view does not provide recommendations or urgency scores. It answers questions. This positions the agent as the epistemic authority and the AI as an assistant with bounded scope -- consistent with the metacommunication goal of supporting agent sensemaking without displacing agent judgment.

The `cited_report_ids` mechanism reinforces this: the AI must show its work, and the agent can inspect it.

---

## 5. Research Agenda and Open Questions

The project surfaces several design problems that remain open and are worth further investigation:

**5.1 Sensemaking trajectory analysis.** The multi-view workspace generates implicit usage data (which views are visited, in what order, what queries are issued). A follow-up study could analyze whether agents develop different sensemaking trajectories depending on entry point (map vs. chat) and whether AI-assisted trajectories lead to different forwarding decisions.

**5.2 Hallucination detection in civic RAG.** The `cited_report_ids` mechanism addresses transparency but not correctness -- an LLM can cite a report that does not actually support its claim. Designing a lightweight faithfulness check for civic-domain RAG (where ground truth is available in the database) is an open engineering problem.

**5.3 Embedding model selection for Brazilian Portuguese civic text.** The multilingual-e5-small model was chosen for memory efficiency. A systematic evaluation of Portuguese-optimized models (e.g., BERTimbau-based) against civic report corpora would inform future deployments.

**5.4 Role boundary communicability.** The three-role system encodes a social contract, but citizens may not understand why they cannot see agent forwardings. A SIM (Semiotic Inspection Method) evaluation of the citizen-facing views would surface communicability breakdowns in the role encoding.

**5.5 AI-assisted development as design documentation.** The plan artifact trail (`_output/plans/`) constitutes a record of design decisions and deferrals. Whether this corpus is useful for post-hoc design rationale reconstruction -- or for training future AI coding assistants on project-specific conventions -- is an open research question.

**5.6 Topic model stability under sparse corpora.** In early deployment, the report corpus is small. BERTopic and TF-IDF produce qualitatively different outputs at low corpus sizes. Characterizing the stability threshold -- below which topic outputs are unreliable -- is a concrete empirical question.

---

## 6. Stack and Reproducibility

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Package management | uv |
| API framework | FastAPI |
| Persistence | SQLite + SQLAlchemy |
| Auth | JWT Bearer (PyJWT), roles: citizen/agent/admin |
| Vector store | ChromaDB |
| Embeddings | sentence-transformers (multilingual-e5-small) |
| Topic modeling | BERTopic / TF-IDF (switchable) |
| LLM (local) | Ollama (`qwen3:8b`) |
| LLM (cloud) | Anthropic API (opt-in via env var) |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS + react-leaflet |
| Testing | pytest (backend), vitest (frontend) |
| Deployment | Docker + Railway (PaaS) |

The system is containerized (Dockerfile at project root) and deployable to Railway with environment variables for LLM provider selection, database URL, and JWT secret. The architecture is reproducible from the public repository; the vector store is gitignored and rebuilt from seed data on first run.

---

## 7. Relation to Course Objectives

fala-gavea was designed to satisfy the AI Systems Design course objectives at multiple levels:

- **AI integration:** three distinct AI subsystems (semantic search, topic modeling, RAG assistant), each with a clean port/adapter boundary
- **Design rationale:** explicit documentation of trade-offs (local vs. cloud LLM, BERTopic vs. TF-IDF, graceful degradation strategy) in plan artifacts
- **Semiotic engineering application:** the multi-view workspace and cited-sources mechanism operationalize metacommunication theory in a working system
- **Civic technology context:** the domain (urban safety demands, public agents, institutional forwardings) provides a realistic context for studying AI-assisted human decision-making in consequential settings

The system is not a prototype -- it is a working application with authentication, persistence, and a deployed frontend. This allows evaluation against real interaction patterns rather than simulated scenarios.

---

*fala-gavea | INF2921/CIS2114 AI Systems Design 2026.1 | Team: Andrey, Mauro, Julia, Herbert, Natali*
