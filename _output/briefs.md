# Briefs Log

DONE | 2026-06-20 23:51 UTC | STARTED | 2026-06-20 23:46 UTC | research | como a atual configuracao docker está adequada a fazer o deploy no railway, considerando modificacoes recentes na stack tecnologica do front end. Segue plano 96

DONE | 2026-06-20 22:58 UTC | STARTED | 2026-06-20 22:49 UTC | implement | 113 | PLAN | 000113

DONE | 2026-06-20 22:42 UTC | STARTED | 2026-06-20 22:35 UTC | plan | Seed de Relatos no painel admin com CSV enriquecido (user_id obrigatorio, auto-cria usuario/topico, fallbacks de coordenada/data/urgencia) | PLAN | 000113

DONE | 2026-06-20 21:27 UTC | STARTED | 2026-06-20 21:21 UTC | implement | Admin Panel page: seed topicos + wipe DB | PLAN | 000112

DONE | 2026-06-20 20:39 UTC | STARTED | 2026-06-20 20:37 UTC | plan | Admin Panel page (CSV upload for topicos, wipe with confirmation dialog, route /admin guarded by admin role) | PLAN | 000112

DONE | 2026-06-20 20:35 UTC | STARTED | 2026-06-20 20:33 UTC | research | is there any frontend view for these operations in feature 109 ?

DONE | 2026-06-20 20:30 UTC | STARTED | 2026-06-20 20:20 UTC | implement | 109 | PLAN | 000109

STARTED | 2026-06-20 16:50 UTC | plan | admin features: seed csv with relatos, topicos, allow wipe all database entries

DONE | 2026-06-20 16:46 UTC | STARTED | 2026-06-20 16:31 UTC | implement | 105 | PLAN | 000105

DONE | 2026-06-19 22:35 UTC | STARTED | 2026-06-19 22:32 UTC | document | --plan 000104 | SHA | HEAD | GENERATED | drr,contextual-help

DONE | 2026-06-19 21:55 UTC | STARTED | 2026-06-19 21:53 UTC | plan | create a api entrypoint to receive a csv with seed relatos. then the use case will bulk insert | PLAN | 000105

DONE | 2026-06-19 22:25 UTC | STARTED | 2026-06-19 21:46 UTC | implement | plan-000104 | PLAN | 000104

DONE | 2026-06-19 21:44 UTC | STARTED | 2026-06-19 21:31 UTC | plan | the 1st frontend iteration — grid/workspace shell + Zustand filter/selection store + lift filter out of MapPage + Mapa/Tabela with cross-filter + wire Tópicos (GET /reports/topics), similares, and RAG chat (POST /chat) to the done backends. Pass source: research-000092 | PLAN | 000104

DONE | 2026-06-19 21:26 UTC | STARTED | 2026-06-19 21:05 UTC | design | formalize JM-TB-003 (explore/filter/analyze journey) in §15 and update §8 UX Patterns with left-rail-filter + swappable-center-views model

DONE | 2026-06-19 21:03 UTC | STARTED | 2026-06-19 20:50 UTC | reflect | 99, 100, 2. Use research log 92 to plan a frontend journey in order to create a relatos filter and visualization amplified with IA tools implemented on backend

DONE | 2026-06-19 18:50 UTC | STARTED | 2026-06-19 18:42 UTC | implement | 100 | PLAN | 000100

DONE | 2026-06-19 | STARTED | 2026-06-19 | plan | roadmap 2 wave 2 item 6 rag-chat | PLAN | 000100

DONE | 2026-06-19 18:51 UTC | STARTED | 2026-06-19 18:39 UTC | implement | 000099 | PLAN | 000099

DONE | 2026-06-19 18:37 UTC | STARTED | 2026-06-19 18:31 UTC | plan | roadmap 2 wave 2. Input on BERTopic: criar espaço semantico para os reports usando o modelo. faz a inferência de topicos a partir de um conjunto de reports, ou seja, retorna os topicos a partir de um conjunto (permite usuario filtrar reports e ver os topicos extraidos dos mesmos) | PLAN | 000099

DONE | 2026-06-19 18:25 UTC | STARTED | 2026-06-19 18:22 UTC | reflect | some IA features are implemented, however in the frontend says Busca semantica (em breve)

DONE | 2026-06-19 17:14 UTC | STARTED | 2026-06-19 17:11 UTC | plan | folowing research 91 lets create a dockerfile to install and run the app locally, preparing to publish the app into Railway. create a mappiong to the db storage to local file | PLAN | 000096

DONE | 2026-06-19 17:23 UTC | STARTED | 2026-06-19 16:56 UTC | reflect | on last implemented plans. I want to test the funcionality. need to re-ingest relatos ficticios | PLAN | 000096

DONE | 2026-06-19 15:04 UTC | STARTED | 2026-06-19 14:50 UTC | implement | plan-000094 | PLAN | 000094

DONE | 2026-06-19 14:02 UTC | STARTED | 2026-06-19 13:25 UTC | check | validate

DONE | 2026-06-19 14:14 UTC | STARTED | 2026-06-19 13:27 UTC | research | criar jornada de visualizacao, busca e analise dos relatos. ao inves do mapa ser o centro da visualizacao, ele eh apenas mais uma forma. o painel central da aplicacao eh um grid, que pode conter diversas ferramentas para visualizar os relatos filtrados. pensar educacionalmente nos dois projetos: (1) Canal Digital Comunitario para Seguranca Urbana (Waze comunitario); (2) Mapa Colaborativo de Dados para Seguranca e Planejamento do Bairro.

DONE | 2026-06-19 13:24 UTC | STARTED | 2026-06-19 13:18 UTC | implement | implement 90 | PLAN | 000090

DONE | 2026-06-19 12:46 UTC | STARTED | 2026-06-19 12:41 UTC | implement | plan-000089 | PLAN | 000089

STARTED | 2026-06-19 12:39 UTC | research | put fala-Gavea app into a open web url server. what are the hosts that allow a dockerfile to be deployed ? maybe we need to create a docker compose structure ?

DONE | 2026-06-19 12:38 UTC | STARTED | 2026-06-19 12:34 UTC | plan | roadmap 2 wave 0 | PLAN | 000089

DONE | 2026-06-18 20:49 UTC | STARTED | 2026-06-18 20:04 UTC | plan | roadmap 1 wave 2: preparar o sistema para operacoes em espaco semantico (busca de similares, RAG, clusterizacao); modelos diferentes por aplicacao (BERTopic para topicos, embeddings para similaridade/RAG); ao criar relato adicionar aos espacos semanticos

DONE | 2026-06-18 19:40 UTC | STARTED | 2026-06-18 19:28 UTC | reflect | estado atual implementado no sistema, frente ao roadmap. o que falta ?

DONE | 2026-06-18 17:36 UTC | STARTED | 2026-06-18 17:29 UTC | implement | 85 | PLAN | 000085

DONE | 2026-06-18 17:08 UTC | STARTED | 2026-06-18 17:03 UTC | plan | seed relatos. quero criar um seed grande, com invervalo de 1 ano de dados. (a api permite entra com data ? ) se n permitir temos que criar diretamente no banco. | PLAN | 000085

DONE | 2026-06-18 16:58 UTC | STARTED | 2026-06-18 16:52 UTC | plan | default users seed scripts admin, citzen01, agente . senha igual ao nome. | PLAN | 000084

DONE | 2026-06-18 16:17 UTC | STARTED | 2026-06-18 14:23 UTC | implement | 82 | PLAN | 000082

DONE | 2026-06-18 14:19 UTC | STARTED | 2026-06-18 14:04 UTC | plan | roadmap 71 item 4: frontend com tecnologias modernas (fugir de paginas estaticas, visual mais fluido e moderno) | PLAN | 000082

DONE | 2026-06-18 13:43 UTC | STARTED | 2026-06-18 13:20 UTC | implement | 79 | PLAN | 000079

DONE | 2026-06-17 22:33 UTC | STARTED | 2026-06-17 22:33 UTC | plan | roadmap 1 item 3 | PLAN | 000079

STARTED | 2026-06-17 22:32 UTC | implement | plan-000075

DONE | 2026-06-17 21:43 UTC | STARTED | 2026-06-17 21:39 UTC | plan | roadmap 1 item 2 | PLAN | 000075

DONE | 2026-06-17 21:42 UTC | STARTED | 2026-06-17 21:37 UTC | research | add external data support via NL query using Overpass API

DONE | 2026-06-17 21:11 UTC | STARTED | 2026-06-17 20:41 UTC | implement | plan-000073 | PLAN | 000073

DONE | 2026-06-17 20:17 UTC | STARTED | 2026-06-17 20:17 UTC | plan | roadmap 1 item 1 complete | PLAN | plan-000073

DONE | 2026-06-17 20:25 UTC | STARTED | 2026-06-17 20:07 UTC | implement | roadmap 1 item 1c

STARTED | 2026-06-17 20:03 UTC | reflect | analise current repo state. this repo was created using a seja plan and roadmap located at _output. what are the next steps ? original plan was execute /design


DONE | 2026-06-19 14:30 UTC | STARTED | 2026-06-19 14:25 UTC | plan | roadmap 2 wave 1 | PLAN | plan-000094
