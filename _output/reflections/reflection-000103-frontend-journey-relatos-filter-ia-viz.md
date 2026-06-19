# Reflection 000103 | 2026-06-19 20:50 UTC | Frontend journey: filtro de relatos + visualização ampliada por IA

## Artifacts reflected on

- [research-000092](../research-logs/research-000092-jornada-grid-visualizacao-relatos.md) — Jornada de grid para visualização, busca e análise dos relatos (JM-TB-003, workspace/grid, linked views)
- [plan-000099](../plans/plan-000099-bertopic-topic-modeling-backend.md) — BERTopic topic modeling backend (`GET /reports/topics`, on-demand sobre o subconjunto filtrado) — DONE
- [plan-000100](../plans/plan-000100-rag-chat-nl-assistant.md) — RAG chat NL assistant backend (`POST /chat`, top-k + `cited_report_ids`) — DONE
- [roadmap-00002](../roadmaps/roadmap-00002-wave2-espacos-semanticos-ia.md) — Wave 2: espaços semânticos especializados por propósito (search/rag vs topics), indexação na criação, backfill, RAG plugável

## Summary

O fio que liga os quatro artefatos: a research-92 desenhou um modelo de **workspace/grid** que inverte o SPA atual *map-centric* — o mapa deixa de ser a visualização e passa a ser um widget entre vários, todos alimentados pelo mesmo conjunto de relatos filtrados via linked views / cross-filtering. Os widgets de IA dessa grid (Tópicos, e implicitamente similares/chat) consomem exatamente os endpoints de backend que os planos 99 e 100 depois construíram: `GET /reports/topics` (BERTopic on-demand sobre o subconjunto filtrado) e o `POST /chat` RAG (top-k + `cited_report_ids`). O roadmap-2 é a espinha que sequenciou esses dois backends, junto com os espaços semânticos especializados por propósito.

A research-92 havia sequenciado os widgets de IA **por último**, atrás de placeholders dignos, porque dependiam de backend ainda não construído (R2). Esses backends agora estão **DONE** — o que é precisamente a condição que torna a jornada de frontend construível agora.

Pontos de ancoragem que a research-92 já deixou prontos para essa jornada:
- **Store de filtro/seleção compartilhado** (Zustand, R1) como contrato *load-bearing* — uma fonte única de verdade do filtro, N widgets que leem o filtro e propõem deltas.
- **Papel define a visibilidade inicial dos widgets, não a estrutura do painel** (R3).
- **Cross-filter em memória + clustering de marcadores** para os ~10k relatos (R5).
- **A11y em todo cross-filter** e **colapso mobile explícito** (R6, R7).
- O widget de Tópicos chama `GET /reports/topics` cada vez que os filtros mudam (plan-099, D-008).

## Reflection

> A jornada basica do usuário e ou pesquisador é a seguinte:
> O painel lateral esquerdo é o estado do filtro dos relatos, nele contém todos os filtros possívels ( por cada, tipo, filtro texto semantico ). Esse conjunto de filtros é aplicado e o resultado desses filtros é visualizado no centro da aplicação. Podemos ter um mapa georeferenciado ( que pode inclusive ser usado como filtro de bbox ), uma lista dos relatos com seu conteúdo descritivo, um painel de busca por outros relatos similares semanticamente desconsiderando os filtros aplicados, uma visualização dos tópicos inferidos, um chat rag com os relatos injetados no contexto.

## Follow-ups

Perguntas em aberto que essa jornada levanta para o futuro plano de frontend (a serem resolvidas em `/design` JM-TB-003 e/ou `/plan`):

- **Painel lateral esquerdo como estado do filtro.** A research-92 falava de uma *FilterBar central*; a reflexão coloca o filtro num **painel lateral esquerdo** persistente. Isso é uma variação de layout sobre o mesmo contrato de store compartilhado, ou uma decisão de layout nova a registrar?
- **Filtro de texto semântico como dimensão de filtro.** A reflexão lista "filtro texto semantico" entre os filtros do painel esquerdo. Hoje o backend tem busca semântica (`ISemanticSearchPort`) e o geojson tem filtros estruturados (tipo/urgência/status/data/bbox). Como o texto semântico entra no mesmo conjunto de filtros — como mais um campo do store que produz um ranking, e como ele se combina com os filtros estruturados?
- **Similares "desconsiderando os filtros aplicados".** Este é o único widget que a reflexão diz explicitamente operar **fora** do filtro central. Como conviver, na mesma grid de linked views, um widget que ignora o filtro com os demais que o respeitam — qual é o seu ponto de entrada (um relato-semente selecionado)?
- **Mapa como filtro de bbox.** A reflexão confirma o bbox-select da research-92 (R5/R6). Fica em aberto o caminho alternativo de teclado/botão para o gesto de arraste (a11y).
- **Chat RAG "com os relatos injetados no contexto".** O `POST /chat` (plan-100) recupera top-k por similaridade. A reflexão sugere injetar **os relatos filtrados** no contexto. É top-k semântico sobre o subconjunto filtrado, ou o conjunto filtrado inteiro? Como isso se reconcilia com o limite de contexto e com `cited_report_ids`?
- **Restrição de papel do chat.** O `POST /chat` está restrito a agent/admin (plan-100). Na jornada "do usuário e/ou pesquisador", o chat aparece como widget central — para quais papéis ele fica visível?
