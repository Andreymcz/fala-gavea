# Research 000170 | FEATURE-X | 2026-06-25 19:36 | DistilBERT classification fine-tuning pipeline and admin tool

tags: distilbert, fine-tuning, ml-pipeline, admin-tool, architecture, nlp

## User Brief

Como podemos arquiteturar uma solucao usando berttopic para ser usada no contexto do gavealab.
Queremos uma ferramenta administrativa para: a partir de um conjunto existente de relatos do
sistema, fazer fine-tunning no modelo pre treinado do bert e disponibiliza-lo para ser usado por
uma feature do sistema para sugerir ReportType de um relato sem a informacao (esta feature
ReportType nullo esta sendo implementada por outro desenvolvedor). Neste research vamos focar em
estruturar o pipeline de fine-tunning e visualizacao do output das informacoes, para ser
visualizadas pelos admins e desenvolvedores.

## Agent Interpretation

Design an end-to-end BERTopic-based classification pipeline for the Fala Gavea system:

1. An admin-triggered pipeline that loads labeled relatos (those with report_type_id != null),
   fits a BERTopic model, persists it, and produces visualization data.
2. An admin dashboard surface (API + frontend) that exposes topic distributions, top terms per
   topic, UMAP scatter data, and topic-to-ReportType mappings.
3. An inference integration point that the null-report_type feature (implemented by another
   developer) can call to suggest a ReportType for unlabeled relatos.

The term "fine-tuning" in this context means fitting BERTopic's clustering and topic
representation pipeline on the domain corpus -- NOT gradient-descent weight updates on the BERT
encoder. This distinction is documented explicitly in the architecture.

## Files Examined

- `src/fala_gavea/infrastructure/topics/bertopic_client.py` -- existing ephemeral BERTopic client
- `src/fala_gavea/domain/repositories/semantic_ports.py` -- ITopicModelPort interface (needs extension)
- `src/fala_gavea/application/use_cases/topics/get_topics_for_reports.py` -- existing use case
- `src/fala_gavea/infrastructure/embeddings/registry.py` -- SemanticConfig dataclass
- `src/fala_gavea/presentation/api/dependencies.py` -- singleton factory pattern (Chroma reference)
- `src/fala_gavea/presentation/api/main.py` -- app entry point, router registration
- `src/fala_gavea/domain/entities/report.py` -- Report entity (report_type_id: str, non-nullable)
- `src/fala_gavea/domain/entities/report_type.py` -- ReportType entity
- `src/fala_gavea/infrastructure/database/models.py` -- SQLAlchemy models
- `pyproject.toml` -- bertopic >=0.17 already in dependencies

---

## Q&A Log

### Q1: How should we architect a BERTopic fine-tuning pipeline and admin visualization tool for Fala Gavea?

**A:**

## Clarification: What "fine-tuning" Means Here

BERTopic is NOT a model you fine-tune via gradient descent. Its pipeline is:

1. Embed texts with a sentence-transformer (weights unchanged by default)
2. Reduce dimensions with UMAP
3. Cluster with HDBSCAN
4. Build topic representations with c-TF-IDF

"Fitting" BERTopic on the relatos corpus = customizing steps 2-4 to the domain data. The
underlying BERT/sentence-transformer weights are NOT updated. This must be documented explicitly
in the codebase (academic clarity requirement).

If actual encoder fine-tuning is desired in a future iteration, it would use
`SentenceTransformerTrainer` from sentence-transformers v3 -- but that requires GPU time and
is out of scope for this pipeline.

---

## Architecture

### Component Map

```
[Admin UI]
    |
    v
POST /admin/topics/fit          <-- trigger training (admin role)
GET  /admin/topics/status       <-- model readiness + metadata
GET  /admin/topics/topic-info   <-- topic list with terms + ReportType mapping
GET  /admin/topics/umap-data    <-- 2D UMAP coords for scatter plot
    |
    v
[Application Layer]
    FitBERTopicModel (use case)
    GetTopicModelStatus (use case)
    |
    v
[Infrastructure Layer]
    BERTopicTrainer (new class)         <-- fits + saves + loads + predicts
    BERTopicClient  (existing, kept)    <-- infer_topics() for ephemeral explore
    |
    v
[Persistence]
    topic_model_data/
        bertopic_model/     <-- BERTopic.save(serialization="safetensors")
        visualization.json  <-- pre-computed at fit time
        metadata.json       <-- training date, corpus_size, num_topics, mode
    |
    v
[Inference hook for null-report_type feature]
    GET /reports/{id}/suggest-type   OR
    POST /reports/suggest-type
        |
        v
    SuggestReportType (use case) -> BERTopicTrainer.predict(text) -> report_type_id | None
```

---

### BERTopic Mode: Zero-Shot (Recommended)

Three candidate modes were evaluated:

| Mode | How it works | Complexity | Fit for this scope |
|------|-------------|------------|-------------------|
| Unsupervised | Discovers latent topics; map to ReportTypes post-hoc | High | Not recommended -- fragile mapping |
| Supervised | Uses report_type_id labels to guide clustering | Medium | Good if all types have >=15 examples |
| Zero-shot | Uses ReportType.name as seed topics | Low | Recommended |

**Recommendation: Zero-shot mode.**

```python
BERTopic(
    zeroshot_topic_list=[rt.name for rt in report_types],
    zeroshot_min_similarity=0.6,
    embedding_model=sentence_transformer,
)
```

Why:
- No secondary mapping step (labels directly correspond to admin-known ReportType names)
- Works even with uneven label distribution
- Results are immediately interpretable by admins
- Eliminates the fragile "topic 3 -> vandalismo" post-hoc assignment problem
- BERTopic >=0.15 supports this natively (project already has >=0.17)

The labeled relatos (those with report_type_id != null) serve as optional evaluation data
(accuracy check post-fit), not as training labels.

---

### New Domain Port: IReportTypeClassifierPort

The existing `ITopicModelPort` conflates two incompatible lifecycles:
- `infer_topics()` -- ephemeral: fit + transform per request, discard model
- `fit()` + `topic_of()` -- persistent: fit once, load model, classify many

Mixing them in one interface violates Interface Segregation and forces
implementors to carry methods they cannot support (stubs raising NotImplementedError).

**Add a second port to `semantic_ports.py`:**

```python
class IReportTypeClassifierPort(ABC):
    @abstractmethod
    def fit(self, reports: list[Report], report_types: list[ReportType]) -> None:
        """Fit the classifier on labeled corpus. Persists model to disk."""
        ...

    @abstractmethod
    def predict(self, text: str) -> str | None:
        """Return predicted report_type_id, or None if model not ready."""
        ...

    @abstractmethod
    def get_visualization_data(self) -> dict:
        """Return pre-computed visualization data for admin dashboard."""
        ...
```

---

### New Infrastructure Class: BERTopicTrainer

File: `src/fala_gavea/infrastructure/topics/bertopic_trainer.py`

Responsibilities:
- `fit(reports, report_types)` -- zero-shot BERTopic fit, writes model + visualization.json + metadata.json
- `load()` -- load persisted model at init or on-demand (lazy)
- `predict(text: str) -> str | None` -- transform single text, return report_type name (None if no model)
- `get_visualization_data() -> dict` -- read pre-computed visualization.json

The model directory is controlled by `FALA_GAVEA_TOPIC_MODEL_DIR` env var (default: `./topic_model_data`).
Add this to `SemanticConfig` in `registry.py`.

**Do NOT modify BERTopicClient.** The existing client handles the exploratory `infer_topics()` path and should stay as-is (minus the NotImplementedError stubs -- see below).

---

### Singleton Wiring in dependencies.py

Follow the exact pattern of `get_report_indexer()`:

```python
_trainer_instance: IReportTypeClassifierPort | None | object = None
_trainer_init_failed = object()
_trainer_lock = threading.Lock()

def get_topic_trainer() -> IReportTypeClassifierPort | None:
    global _trainer_instance
    if _trainer_instance is _trainer_init_failed:
        return None
    if _trainer_instance is not None:
        return _trainer_instance
    with _trainer_lock:
        if _trainer_instance is not None:
            return None if _trainer_instance is _trainer_init_failed else _trainer_instance
        try:
            from fala_gavea.infrastructure.topics.bertopic_trainer import BERTopicTrainer
            from fala_gavea.infrastructure.embeddings.registry import SemanticConfig
            _trainer_instance = BERTopicTrainer(SemanticConfig())
        except Exception as exc:
            _log.warning("BERTopicTrainer unavailable: %s", exc)
            _trainer_instance = _trainer_init_failed
    return None if _trainer_instance is _trainer_init_failed else _trainer_instance
```

Graceful degradation: if no model artifact exists at startup, `predict()` returns `None`.
The null-report_type feature should handle `None` as "no suggestion available."

---

### Admin API Router: /admin/topics

New file: `src/fala_gavea/presentation/api/routers/admin_topics.py`

```
POST /admin/topics/fit
    - Role: admin
    - Returns: 202 Accepted {"job_id": "...", "status": "running"}
    - Protected by threading.Lock (returns 409 if training in progress)
    - Uses FastAPI BackgroundTasks to run BERTopicTrainer.fit() async

GET /admin/topics/fit/{job_id}
    - Role: admin
    - Returns: {"status": "running"|"done"|"failed", "error": "..."}
    - In-memory job status dict (sufficient for educational scope)

GET /admin/topics/status
    - Role: admin
    - Returns: {"model_ready": bool, "trained_at": ..., "corpus_size": int, "num_topics": int}

GET /admin/topics/topic-info
    - Role: admin
    - Returns: [{topic_id, label, terms, count, report_type_name}]
    - Reads from visualization.json (pre-computed at fit time)

GET /admin/topics/umap-data
    - Role: admin
    - Returns: [{doc_id, x, y, topic_id, report_type_id, text_snippet}]
    - Reads from visualization.json (pre-computed at fit time)
```

Add `"admin"` to `_API_PREFIXES` in `main.py` (currently missing; needed for SPA middleware).
Mount: `app.include_router(admin_topics_router.router, prefix="/admin/topics", tags=["admin"])`

---

### visualization.json Schema

Written at fit time, read by admin GET endpoints:

```json
{
  "metadata": {
    "trained_at": "2026-06-25T19:00:00Z",
    "corpus_size": 4800,
    "num_topics": 8,
    "mode": "zeroshot"
  },
  "topics": [
    {
      "topic_id": 0,
      "label": "vandalismo",
      "report_type_id": "rt-uuid-...",
      "terms": ["pixacao", "quebrado", "destruicao", "parede"],
      "count": 312
    }
  ],
  "umap_points": [
    {
      "doc_id": "relato-uuid-...",
      "x": -3.14,
      "y": 2.71,
      "topic_id": 0,
      "report_type_id": "rt-uuid-...",
      "snippet": "Pixacao na calçada da rua..."
    }
  ]
}
```

Prefer pre-computed over on-the-fly: the BERTopic model loaded in memory for a single
admin page load can occupy 100-500 MB. Pre-computing at fit time eliminates this overhead
and keeps the dashboard snappy.

---

### Inference Integration Point (for null-report_type feature)

New use case: `src/fala_gavea/application/use_cases/topics/suggest_report_type.py`

```python
class SuggestReportType:
    def __init__(self, classifier: IReportTypeClassifierPort | None) -> None:
        self._classifier = classifier

    def execute(self, text: str) -> str | None:
        if self._classifier is None:
            return None
        return self._classifier.predict(text)
```

The other developer (implementing null-report_type) can call this use case when
`report_type_id` is None on a newly submitted relato. The response `None` means
"no model available, ask the user to specify manually."

---

### Frontend Admin Page (Visualization)

New page in the React SPA: `/admin/topics`

Suggested components:
1. **Model Status Card** -- trained date, corpus size, num topics; "Trigger Re-training" button
2. **Topic Bar Chart** (Recharts BarChart) -- topic labels on X axis, document count on Y axis, colored bars with top 5 terms as tooltip
3. **UMAP Scatter Plot** -- 2D scatter colored by topic/ReportType; tooltip shows text snippet
4. **Topic-ReportType Table** -- topic_id, label, top terms, count, mapped ReportType name

The existing React + Vite + Tailwind + recharts/leaflet stack can support all of these.
The scatter plot can use a simple SVG or recharts ScatterChart.

---

### Changes to Existing BERTopicClient

Remove the `NotImplementedError` stubs from `fit()`, `topic_of()`, `list_topics()`.
These are production-facing and cause confusing failures. Options:
- If `BERTopicClient` no longer needs to implement `ITopicModelPort` fully, make it
  implement only a narrower interface or remove the ABC inheritance.
- Add a class docstring clarifying: "`infer_topics()` is the only supported method;
  use `BERTopicTrainer` for persistent classification."

---

### Test Strategy

BERTopic is non-deterministic (UMAP + HDBSCAN vary across runs). Test strategy:

- **Unit tests**: mock `IReportTypeClassifierPort` with `unittest.mock.MagicMock`.
  Test use case logic and router behavior independently.
- **Integration tests**: pre-save a minimal fixture model (fit on ~20 synthetic relatos)
  at `tests/fixtures/topic_model/`. Load fixture in `BERTopicTrainer` test factory.
  Test `predict()` returns a string matching a known ReportType name.
- **Training path**: test that `fit()` runs without error on small corpus, writes expected
  files, and `load()` + `predict()` works structurally.
- Do NOT assert specific topic IDs -- only assert structural correctness.

---

---

## Critical Finding: Existing Training Work (Discovered During Research)

During research, the following untracked local files were found (not yet committed to git):

- `scripts/train_topic_classifier.ipynb` -- Jupyter notebook with a complete training pipeline
- `models/topic_classifier/` -- Trained model directory with 11+ checkpoints + best model
- `data/seed_relatos_fala_gavea_1k.csv` -- 1k seed CSV used for training

**The team has already implemented actual BERT fine-tuning** -- NOT BERTopic. The approach:
- Model: `distilbert/distilbert-base-multilingual-cased` via HuggingFace Transformers
- Gradient-descent fine-tuning with `Trainer` API (real weight updates)
- 5000 relatos, 80/20 stratified split, EarlyStoppingCallback
- Best model saved to `models/topic_classifier/best/` (safetensors format)
- `label_map.json` defines 7 topic labels:
  - 0: Conflito social
  - 1: Espaco publico
  - 2: Iluminacao publica
  - 3: Lixo e conservacao
  - 4: Seguranca e circulacao
  - 5: Transito e mobilidade
  - 6: Vandalismo
- Notebook includes visualization: confusion matrix (seaborn) + classification report
- `TopicClassifier` helper class already written in the notebook

**This shifts the research scope:** The fine-tuning pipeline is DONE. The remaining work is:
1. Integrate the existing model into clean architecture
2. Expose the visualization data via admin API
3. Wire inference into the null-report_type feature
4. Resolve the label mismatch (see below)

### Label Mismatch: Classifier Labels vs System ReportTypes

The 7 classifier labels (e.g., "Lixo e conservacao") may NOT match the `report_type.name`
values in the production DB. A mapping layer is required:

```
classifier output label  ←→  report_type_id (FK to report_types table)
```

Options for the mapping:
A. **Static JSON config** -- manually map label names to report_type_ids (admin creates once)
B. **Admin UI mapping** -- expose a mapping UI where admin pairs each label to a ReportType
C. **Name normalization** -- normalize both classifier label and report_type.name (lowercase,
   remove accents, strip spaces) and match automatically; flag ambiguities

Recommendation: start with C (auto-match by normalized name), fall back to B (admin confirmation)
when normalization fails. Store the resolved mapping in a `label_to_report_type.json` file
alongside the model, editable by admin via the UI.

### Revised Infrastructure Class: DistilBERTClassifier

Given the existing notebook, the infrastructure class should wrap the notebook's `TopicClassifier`:

File: `src/fala_gavea/infrastructure/topics/distilbert_classifier.py`

```python
class DistilBERTClassifier(IReportTypeClassifierPort):
    """Wraps the fine-tuned DistilBERT model from models/topic_classifier/best/.

    'Fine-tuning' here = gradient-descent weight updates on distilbert-base-multilingual-cased
    using labeled relatos corpus (Trainer API). Model loaded from disk at init.
    """

    def __init__(self, config: SemanticConfig) -> None:
        model_dir = Path(config.topic_model_dir) / "best"
        if not model_dir.exists():
            raise FileNotFoundError(f"No trained model at {model_dir}")
        self._tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
        self._model = AutoModelForSequenceClassification.from_pretrained(str(model_dir))
        self._model.eval()
        label_map_path = model_dir.parent / "label_map.json"
        self._label_map: dict[int, str] = {
            int(k): v for k, v in json.loads(label_map_path.read_text()).items()
        }
        mapping_path = model_dir.parent / "label_to_report_type.json"
        self._label_to_rt: dict[str, str] = (
            json.loads(mapping_path.read_text()) if mapping_path.exists() else {}
        )

    def predict(self, text: str) -> str | None:
        inputs = self._tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
        with torch.no_grad():
            logits = self._model(**inputs).logits
        probs = logits.softmax(dim=-1)[0]
        label_id = int(probs.argmax().item())
        label = self._label_map[label_id]
        return self._label_to_rt.get(label)  # None if mapping not configured
```

### Revised Visualization: Expose Notebook Outputs via API

The notebook already generates:
- Classification report (precision, recall, F1 per class)
- Confusion matrix data
- Per-prediction examples (acertos/erros)

Instead of re-computing at admin dashboard load time, save these as JSON at training time.
Add a new export step to the notebook:

```python
# Save evaluation results as visualization.json (to be served by admin API)
import json
from sklearn.metrics import classification_report, confusion_matrix

cr = classification_report(true_labels, preds, target_names=le.classes_,
                           output_dict=True, zero_division=0)
cm = confusion_matrix(true_labels, preds).tolist()

viz = {
    "trained_at": ...,
    "model_name": MODEL_NAME,
    "dataset_size": len(df),
    "num_classes": num_labels,
    "classes": le.classes_.tolist(),
    "classification_report": cr,
    "confusion_matrix": cm,
    "split": {"train": len(train_df), "val": len(val_df)},
}
(OUTPUT_DIR / "visualization.json").write_text(json.dumps(viz, ensure_ascii=False, indent=2))
```

### Dependencies to Add

HuggingFace transformers and torch are NOT in `pyproject.toml` yet (used only in notebook).
For the infrastructure class, they need to be added:

```toml
"transformers>=4.40",
"torch>=2.0",
```

Note: `torch` is CPU-only currently (`CUDA disponivel: False`). This is acceptable for inference
at low QPS. For re-training, the same CPU path works (slow but functional for 5k examples).

---

## Recommendations Summary

| Priority | Recommendation |
|----------|---------------|
| HIGH | Add `IReportTypeClassifierPort` to `semantic_ports.py` with `predict(text) -> str | None` and `get_visualization_data() -> dict` |
| HIGH | Create `DistilBERTClassifier` in `infrastructure/topics/distilbert_classifier.py` wrapping the existing model at `models/topic_classifier/best/` |
| HIGH | Commit the notebook and model directory; add `models/topic_classifier/best/` to git (not the checkpoints -- those can be gitignored); add `models/` to `.gitignore` except for `models/topic_classifier/best/` and `models/topic_classifier/label_map.json` |
| HIGH | Add label-to-report_type mapping layer: `models/topic_classifier/label_to_report_type.json`; implement auto-match by normalized name; expose admin endpoint to view/edit the mapping |
| HIGH | Add `topic_model_dir` to `SemanticConfig` (default: `./models/topic_classifier`); wire `get_topic_trainer()` singleton into `dependencies.py` (replace current `return None` stub) |
| HIGH | Add `transformers>=4.40` and `torch>=2.0` to `pyproject.toml` dependencies |
| MEDIUM | Export `visualization.json` from the notebook at training time (classification report + confusion matrix as JSON); serve via `GET /admin/topics/visualization` |
| MEDIUM | Add admin React page at `/admin/topics` with: confusion matrix heatmap, per-class F1 bar chart, label-to-ReportType mapping editor |
| MEDIUM | Add `SuggestReportType` use case (thin wrapper over `IReportTypeClassifierPort.predict()`); integrate into report creation flow when `report_type_id` is None |
| MEDIUM | Remove `NotImplementedError` stubs from `BERTopicClient.fit/topic_of/list_topics` or clarify they are reserved for future exploratory mode |
| LOW | Add `"topic_model": "ready"|"not_trained"|"error"` to `/health` response |
| LOW | If re-training via API is desired later: add `POST /admin/topics/fit` with BackgroundTasks; for now a notebook re-run is sufficient |
