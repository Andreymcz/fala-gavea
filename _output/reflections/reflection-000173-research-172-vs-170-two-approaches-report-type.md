# Reflection 000173 | 2026-06-25 20:42 UTC | research 172 vs 170: dois mecanismos de sugestão de report_type

## Artifacts reflected on

- [research-000172](../research-logs/research-000172-ai-suggest-report-type.md) — AI-assisted report_type suggestion via ChromaDB semantic similarity
- [research-000170](../research-logs/research-000170-distilbert-classification-pipeline-admin-tool.md) — DistilBERT classification pipeline and admin tool

## Summary

**research-000172** mapeou o design completo para sugerir `report_type` a partir de similaridade semântica no ChromaDB: nova porta `IReportTypeSuggestionPort`, coleção `falagavea_report_types` indexada por nome/descrição dos tipos, endpoint `PATCH /reports/{id}/report-type` para confirmação por agente/admin, campo de proveniência `report_type_source`, sentinela `"unknown"` para evitar migração de schema, e fila de revisão com threshold de confiança (0.65). Mecanismo leve, sem treinamento, síncrono na criação do relato.

**research-000170** começou como design de pipeline BERTopic mas descobriu, no meio da sessão, que a equipe já havia executado fine-tuning real por gradiente descendente (`distilbert-base-multilingual-cased`, 5k relatos, 7 labels, checkpoint em `models/topic_classifier/best/`). O escopo se converteu em integrar o modelo existente: nova porta `IReportTypeClassifierPort`, classe `DistilBERTClassifier`, mapeamento `label_to_report_type.json` para resolver o mismatch entre labels do classificador e `report_type.name` no banco, e página admin com matriz de confusão e editor de mapeamento.

Os dois pesquisam a mesma necessidade de negócio (sugerir tipo quando ausente) por caminhos técnicos distintos: 172 via busca semântica no espaço dos tipos cadastrados, 170 via inferência de um modelo ML treinado no corpus de relatos.

## Reflection

seria muito interessante ter as 2 opcoes e comparar o resultado delas

## Follow-ups

- As duas portas (`IReportTypeSuggestionPort` de 172 e `IReportTypeClassifierPort` de 170) são paralelas e podem coexistir no sistema ao mesmo tempo — o que abre a possibilidade de um experimento A/B ou de uma estratégia de ensemble (fallback de um para o outro quando confiança baixa).
- A comparação empírica das duas abordagens exigiria um conjunto de avaliação: relatos com `report_type_id` conhecido, usados como ground-truth para medir acurácia de cada mecanismo independentemente.
- O threshold de confiança (0.65 em 172) e o score de probabilidade softmax (170) têm escalas e interpretações distintas — uma comparação justa precisaria normalizar essas métricas ou usar uma métrica comum (ex.: top-1 accuracy no conjunto de avaliação).
- O mismatch de labels de 170 (7 labels vs. tipos no banco) e o sentinela de 172 ("unknown") são dois pontos de fricção distintos que precisariam ser resolvidos antes de qualquer comparação significativa.
- Uma futura `/research` poderia explorar: qual dos dois mecanismos acerta mais nos relatos do seed CSV? Onde eles discordam?
