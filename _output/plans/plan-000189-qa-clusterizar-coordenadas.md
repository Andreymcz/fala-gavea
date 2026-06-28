# QA Log | plan-000189 | Clusterizar coordenadas dos relatos em POIs da Gávea

## Brief

ajustes no seed: o bounding box dos relatos estão pegando uma parte do jardim botânico e lagoa. Vamos clusterizar estes relatos... colocar na rocinha-gávea, parque da cidade, puc etc.

## Q&A log

**Q (decisão — clusters):** Quais POIs da Gávea devem virar centros de cluster?
**A:** 7 POIs (Rocinha, PUC-Rio, Baixo Gávea/Pç. Santos Dumont, Parque da Cidade, Shopping da Gávea, Planetário, Jockey Club) — boa cobertura espacial do bairro.

**Q (decisão — distribuição):** Como distribuir os relatos entre os clusters?
**A:** Ponderada (hotspots): Rocinha (peso 8) e PUC (6) concentram mais relatos; demais com peso menor — o mapa conta uma história de áreas de maior demanda.

## Notas de implementação

- Causa raiz: `generate_natural_relatos.py` amostrava `random.uniform` num retângulo `lat ∈ [-22.985,-22.950]`, `lon ∈ [-43.240,-43.200]` que vazava a NE (Jardim Botânico/Lagoa).
- Solução: módulo único `scripts/gavea_clusters.py` (POIs + pesos + `GAVEA_BBOX` + `sample_coordinate` com clamp à bbox). Gerador e `recluster_coordinates.py` consomem o módulo.
- CSVs commitados (200/1k/5k) e âncoras re-clusterizados reescrevendo só lat/lon (determinístico por índice de linha; texto/data/tópico/urgência preservados). Menções a ruas fora da Gávea (Pacheco Leão, Rua Jardim Botânico, Av. Epitácio Pessoa, Rua São Clemente) trocadas por ruas da Gávea.
- Demo do agent-worklist preservada (10 relatos "Iluminacao publica" desde 2026-05-29).
- Regressão: `tests/scripts/test_seed_coordinates_in_gavea.py` afirma `in_gavea` em todas as fontes. Suíte completa: 317 passed; ruff limpo.
