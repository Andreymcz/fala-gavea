# DONE | 2026-06-28 22:40 UTC | Plan 000189 | TOOLING-X | 2026-06-28 22:20 | Clusterizar coordenadas dos relatos em POIs reais da Gávea | Review: light
plan_format_version: 1

## Brief

ajustes no seed: o bounding box dos relatos estão pegando uma parte do jardim botânico e lagoa. Vamos clusterizar estes relatos... colocar na rocinha-gávea, parque da cidade, puc etc.

## Agent Interpretation

Hoje as coordenadas dos relatos são geradas por **amostragem uniforme dentro de um retângulo** (`lat ∈ [-22.985, -22.950]`, `lon ∈ [-43.240, -43.200]` em `scripts/generate_natural_relatos.py:266-267`). Esse retângulo vaza para o **nordeste** — sobre o Jardim Botânico e a Lagoa Rodrigo de Freitas — e espalha milhares de pontos fora da Gávea. O mapa centra em `GAVEA_CENTER = [-22.9731, -43.2272]` (`frontend/src/features/workspace/views/MapView.tsx:16`).

A correção: substituir a amostragem uniforme por **clusterização em torno de POIs reais da Gávea**. Cada relato é atribuído a um cluster (escolha **ponderada**) e recebe um *jitter* gaussiano pequeno (~130m) em volta do centro, mantendo tudo dentro da Gávea e longe do Jardim Botânico/Lagoa.

**Decisões confirmadas com o usuário:**
- **7 POIs** como centros de cluster (cobertura espacial do bairro).
- **Distribuição ponderada** (hotspots): Rocinha e PUC concentram mais relatos; demais POIs com peso menor — o mapa conta uma história de áreas de maior demanda.

### Fontes de coordenadas a corrigir (levantamento)

| Fonte | Mecanismo | Situação atual |
|---|---|---|
| `scripts/generate_natural_relatos.py` | `random.uniform` retângulo | **Causa raiz** — gera o CSV 1k (e 5k via ajuste de `TOTAL_PER_TOPIC`) |
| `data/seed_relatos_fala_gavea_200.csv` | CSV curado (textos narrativos) | Coords espalhadas, algumas na Lagoa (ex.: `-43.2059`) |
| `data/seed_relatos_fala_gavea_1k.csv` | gerado | Espalhado pelo retângulo |
| `data/seed_relatos_fala_gavea_5k.csv` | gerado | Espalhado pelo retângulo |
| `data/seed_journey_anchors.csv` | curado (demo agent-worklist) | Várias âncoras derivam para NE (`lon` até `-43.2158`); textos citam ruas do Jardim Botânico (ex.: anchor03 "Pacheco Leão com Rua Jardim Botanico") |
| `scripts/seed_citizen01.py` (`_RELATOS`) | coords hardcoded (10) | Várias fora da Gávea (ex.: "Av. Epitácio Pessoa" = Lagoa; "Rua São Clemente" = Botafogo) |

### Cluster set (7 POIs) + pesos

Coordenadas todas dentro da Gávea (`lat ≤ -22.974`, `lon ≤ -43.224`), com folga em relação ao Jardim Botânico/Lagoa (que ficam a NE = `lat` e `lon` menos negativos). PUC-Rio verificado em fonte externa (`-22.9783, -43.2334`).

| POI | lat | lon | peso |
|---|---|---|---|
| Rocinha (borda Estrada da Gávea) | -22.9870 | -43.2455 | 8 |
| PUC-Rio | -22.9783 | -43.2334 | 6 |
| Baixo Gávea / Pç. Santos Dumont | -22.9748 | -43.2300 | 4 |
| Parque da Cidade (Gávea) | -22.9800 | -43.2420 | 3 |
| Shopping da Gávea | -22.9765 | -43.2320 | 3 |
| Planetário / V.-Gov. Rubens Berardo | -22.9762 | -43.2262 | 2 |
| Jockey Club (Hipódromo) | -22.9762 | -43.2248 | 2 |

**Jitter:** gaussiano `σ = 0.0009` (~100m), com *clamp* à bounding box da Gávea para garantir que nenhum ponto vaze.

**Gávea bounding box (validação):** `lat ∈ [-22.990, -22.972]`, `lon ∈ [-43.248, -43.224]`. Qualquer coordenada com `lat > -22.972` ou `lon > -43.224` está derivando para Lagoa/Jardim Botânico e falha a verificação.

## Constraints & Conventions

- **Fonte única de verdade.** Definições de cluster (POIs, pesos, bbox, sampler) vivem em **um** módulo (`scripts/gavea_clusters.py`); gerador, recluster e checagem importam dele — nada de coordenadas duplicadas.
- **Determinístico / diff-reviewável.** O recluster usa RNG semeado por índice de linha, para que rodar de novo produza o mesmo resultado e o diff dos CSVs commitados seja estável e revisável.
- **Preservar texto curado.** Re-clusterizar reescreve **apenas** as colunas `latitude`/`longitude`; texto, data, tópico e urgência permanecem intactos.
- **Preservar a demo.** A ordem das linhas, datas, tópicos e urgências de `seed_journey_anchors.csv` não mudam — a query do agent-worklist (statuses `pendente`/`em_analise`, since `2026-05-29`, tipo "Iluminacao publica") continua retornando o mesmo conjunto.
- **Type annotations** obrigatórias em funções públicas (`CONVENTION_3`).
- Sem caminhos hardcoded fora do módulo de clusters; CLIs recebem `--csv`.

## Steps

### Step 1: Módulo de clusters da Gávea (fonte única)
Criar `scripts/gavea_clusters.py` com a fonte única de verdade da clusterização:
- `CLUSTERS: list[Cluster]` — uma `Cluster` (dataclass ou NamedTuple) por POI com `name: str`, `lat: float`, `lon: float`, `weight: int`, conforme a tabela em Agent Interpretation (7 POIs, pesos 8/6/4/3/3/2/2).
- `GAVEA_BBOX` — constantes `LAT_MIN=-22.990`, `LAT_MAX=-22.972`, `LON_MIN=-43.248`, `LON_MAX=-43.224`.
- `JITTER_SIGMA = 0.0009`.
- `sample_coordinate(rng: random.Random) -> tuple[float, float]` — escolhe um cluster por peso (`rng.choices`), aplica jitter gaussiano (`rng.gauss`) em lat e lon, faz *clamp* à bbox e arredonda a 6 casas.
- `in_gavea(lat: float, lon: float) -> bool` — True se a coordenada está dentro de `GAVEA_BBOX`.

Módulo puro (só `random`/`dataclasses`), sem dependências de rede/DB.
- **Files**: `scripts/gavea_clusters.py` (create), `tests/scripts/test_gavea_clusters.py` (create)
- **References**: `project/standards.md § Backend`
- **Interface**: exports `CLUSTERS`, `GAVEA_BBOX`, `sample_coordinate(rng: random.Random) -> tuple[float, float]`, `in_gavea(lat: float, lon: float) -> bool`
- **Verify**: `uv run pytest tests/scripts/test_gavea_clusters.py` passa
- **Tests**: quando 10.000 coordenadas são amostradas com `random.Random(0)`, todas satisfazem `in_gavea(...)` (nenhuma vaza para Jardim Botânico/Lagoa) e a distribuição por cluster mais próximo respeita aproximadamente os pesos (Rocinha e PUC são os dois mais frequentes)

### Step 2: Gerador usa o módulo de clusters
Refatorar `scripts/generate_natural_relatos.py` para gerar coordenadas via clusterização em vez do retângulo uniforme. Remover as linhas `lat = round(random.uniform(-22.985, -22.950), 6)` / `lon = round(random.uniform(-43.240, -43.200), 6)` (linhas ~266-267) e usar `sample_coordinate(rng)` do novo módulo. Semear um `random.Random` determinístico no início de `main()` para que regenerações sejam estáveis. Manter o resto do gerador (templates, datas, urgências) inalterado.
- **Files**: `scripts/generate_natural_relatos.py` (modify)
- **References**: `project/standards.md § Backend`
- **Depends on**: Step 1
- **Verify**: `uv run python scripts/generate_natural_relatos.py` produz `data/seed_relatos_fala_gavea_1k.csv` cujas coordenadas passam todas em `in_gavea(...)`
- **Tests**: N/A (coberto pela checagem de bbox no Step 5)

### Step 3: Script de recluster + aplicar aos CSVs em massa
Criar `scripts/recluster_coordinates.py`: CLI que lê um CSV de relatos, reescreve **apenas** `latitude`/`longitude` de cada linha via `sample_coordinate`, preservando todas as demais colunas, e grava de volta. RNG semeado de forma estável por índice de linha (ex.: `random.Random(row_index)`) para diffs reproduzíveis. Aceita `--csv PATH` repetível; default = os três CSVs em massa. Em seguida, executar nos três CSVs commitados (`200`, `1k`, `5k`) para reescrever as coordenadas espalhadas.
- **Files**: `scripts/recluster_coordinates.py` (create), `data/seed_relatos_fala_gavea_200.csv` (modify), `data/seed_relatos_fala_gavea_1k.csv` (modify), `data/seed_relatos_fala_gavea_5k.csv` (modify)
- **References**: `project/standards.md § Backend`
- **Depends on**: Step 1
- **Verify**: após rodar, as 3 colunas de coordenadas dos três CSVs passam todas em `in_gavea(...)`; colunas `texto_relato`/`data`/`topico`/`urgency` permanecem byte-idênticas (diff só nas colunas de coordenada)
- **Tests**: N/A (coberto pela checagem de bbox no Step 5)

### Step 4: Re-clusterizar fontes curadas (âncoras + citizen01)
Realinhar as duas fontes curadas/hardcoded à Gávea, preservando seu papel na demo:
- `data/seed_journey_anchors.csv`: reescrever só `latitude`/`longitude` (reusar `recluster_coordinates.py`), **mantendo** ordem das linhas, `data`, `topico`, `urgency` — a query do agent-worklist deve continuar retornando o mesmo conjunto. **Caveat de texto:** anchor03 cita "Rua Pacheco Leão com a Rua Jardim Botanico" (ruas do Jardim Botânico); ao realocar a coordenada para a Gávea, trocar a menção de rua no texto por uma da Gávea (ex.: "Rua Marquês de São Vicente com a Estrada da Gávea") para manter coerência texto↔mapa.
- `scripts/seed_citizen01.py`: substituir os 10 pares `lat`/`lon` hardcoded em `_RELATOS` por coordenadas alinhadas aos centros de cluster (com pequeno jitter, escolhidos manualmente para distribuir entre POIs). Ajustar as menções de rua que apontam para fora da Gávea ("Avenida Epitácio Pessoa" → Lagoa; "Rua São Clemente" → Botafogo) para ruas da Gávea, mantendo o sentido do relato.
- **Files**: `data/seed_journey_anchors.csv` (modify), `scripts/seed_citizen01.py` (modify)
- **References**: `project/standards.md § Backend`
- **Depends on**: Step 3
- **Verify**: coordenadas de ambas as fontes passam em `in_gavea(...)`; a query do agent-worklist seedada continua retornando ≥10 relatos (conforme `CLAUDE.md § Demo journeys`)
- **Tests**: N/A (coberto pela checagem de bbox no Step 5)

### Step 5: Verificação de bbox + atualização de docs
Adicionar uma checagem reutilizável que falha se qualquer coordenada seedada vazar para fora da Gávea, e documentar o novo fluxo:
- `tests/scripts/test_seed_coordinates_in_gavea.py`: parametrizado sobre os três CSVs em massa, `seed_journey_anchors.csv` e os `_RELATOS` de `seed_citizen01.py`; afirma `in_gavea(lat, lon)` para toda linha. Isso captura regressões futuras (alguém regenera com o retângulo antigo) automaticamente.
- `CLAUDE.md`: na seção de seed, mencionar que as coordenadas são clusterizadas em POIs da Gávea via `scripts/gavea_clusters.py`, e como regenerar (`generate_natural_relatos.py`) / re-clusterizar (`recluster_coordinates.py`).
- **Files**: `tests/scripts/test_seed_coordinates_in_gavea.py` (create), `CLAUDE.md` (modify)
- **References**: `project/standards.md § Backend`
- **Depends on**: Step 2, Step 3, Step 4
- **Verify**: `uv run pytest tests/scripts/test_seed_coordinates_in_gavea.py` passa; `uv run ruff check scripts/ tests/` limpo
- **Tests**: este passo É o teste de regressão (checagem de bbox sobre todas as fontes seedadas)
- **Docs**: atualizar `CLAUDE.md § Build & Run` (seed) com o fluxo de clusterização

## Validation

1. `uv run pytest tests/scripts/` — clusters + checagem de bbox passam.
2. `uv run ruff check scripts/ tests/` — limpo.
3. Visual (opcional, recomendado): `make seed` num servidor local e abrir o mapa (`/`) — os pontos devem formar grupos visíveis sobre Rocinha/PUC/Parque da Cidade etc., sem nuvem sobre o Jardim Botânico/Lagoa.
4. Demo intacta: `uv run python scripts/seed_journey_anchors.py` e confirmar que a query do agent-worklist ainda retorna ≥10 relatos.

## Suggestions (fora do escopo)

- **Polígono real da Gávea** em vez de bounding box retangular: a bbox de validação ainda é um retângulo (mais apertado). Se a precisão importar, validar contra o GeoJSON do bairro.
- **Centros de cluster em config**: hoje no módulo Python; poderiam virar um pequeno JSON/YAML em `data/` se designers não-devs forem ajustar POIs.
- **Pesos por tópico**: além de ponderar por POI, ponderar combinações tópico×POI (ex.: mais "Lixo" perto do Shopping, mais "Conflito social" perto da Rocinha) para realismo temático.

## Implementation Summary (2026-06-28, manual mode)

Todos os 5 passos concluídos. **9 testes novos passam; suíte completa 317 passed; ruff limpo.**

- [x] **Step 1** — `scripts/gavea_clusters.py` (fonte única: 7 POIs ponderados, `GAVEA_BBOX`, `sample_coordinate`, `in_gavea`, `nearest_cluster`) + `tests/scripts/test_gavea_clusters.py` (4 testes).
- [x] **Step 2** — `generate_natural_relatos.py` usa `sample_coordinate` (RNG semeado, `argv[1]` opcional para saída). Verificado: 1000 linhas geradas, 0 fora da Gávea.
- [x] **Step 3** — `scripts/recluster_coordinates.py` (determinístico por índice de linha) aplicado a `200/1k/5k`. Word-diff confirma: só lat/lon mudaram; 0 fora da Gávea.
- [x] **Step 4** — `seed_journey_anchors.csv` re-clusterizado (demo intacta: 10 relatos "Iluminacao publica" desde 2026-05-29) + textos de ruas do Jardim Botânico (Pacheco Leão / Rua Jardim Botânico) trocados por ruas da Gávea. `seed_citizen01.py`: 10 coords realinhadas + menções "Av. Epitácio Pessoa"/"Rua São Clemente" trocadas por ruas da Gávea.
- [x] **Step 5** — `tests/scripts/test_seed_coordinates_in_gavea.py` (regressão sobre 3 CSVs + âncoras + citizen01) + `CLAUDE.md` atualizado com o fluxo de clusterização.

### Decisões de implementação
- O test loader registra o módulo em `sys.modules` antes de `exec_module` (necessário para `@dataclass` resolver via importlib). Uso normal (`import gavea_clusters` de scripts irmãos) não precisa disso.
- Para evitar churn de texto nos CSVs commitados, o gerador **não** sobrescreve o 1k commitado na verificação (saída para arquivo temporário via `argv[1]`); os CSVs commitados são alterados apenas pelo recluster (só colunas de coordenada).

### Não feito (de propósito)
- Polígono real da Gávea, centros em config externa, e pesos por tópico permanecem em Suggestions (fora de escopo).
