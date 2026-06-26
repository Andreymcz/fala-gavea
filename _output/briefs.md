# Briefs Log

DONE | 2026-06-26 12:25 UTC | STARTED | 2026-06-26 12:22 UTC | plan | source: research-000176 Deliverable B — forwarding comment synthesis (SummarizeForwardingComments via ILLMClient, POST /forwardings/{id}/comments/summary agent-only, ephemeral, prompt-injection hardening) | PLAN | 000179

DONE | 2026-06-26 12:25 UTC | STARTED | 2026-06-26 12:22 UTC | plan | source: research-000176 Deliverable A — reusable AiBadge AI-provenance marker component applied at chat/NL-filter+semantic/report-type-suggestion sites | PLAN | 000178

DONE | 2026-06-26 11:55 UTC | STARTED | 2026-06-26 11:40 UTC | research | ADD IA marker on all features on site that use IA para sugerir algo (ReportTypes), síntese de comentarios de encaminhamentos (não temos — planejar)

DONE | 2026-06-26 11:47 UTC | STARTED | 2026-06-26 14:37 UTC | research | chat helper para usuário acoplado ao sistema que acessa um corpus de documentação gerada no projeto (planos/research/communications do SEJA + casos de uso + o que foi implementado), enriquecido com RAG, como assistente de comunicação do que é a plataforma

DONE | 2026-06-25 21:40 UTC | STARTED | 2026-06-25 21:35 UTC | plan | source:research 172 vamos planejar a implementacao da feature de sugestao de reporttype. vamos arquiteturar de forma que seja simples trocar as 2 abordagens chromadb e distilbert. o fine-tunning sera feito offline | PLAN | 000174

DONE | 2026-06-25 20:43 UTC | STARTED | 2026-06-25 20:34 UTC | reflect | on research 172 and 170 and its differences

DONE | 2026-06-25 19:39 UTC | STARTED | 2026-06-25 19:25 UTC | research | AI-assisted report_type suggestion: map the full design space — nullable report_type_id migration, SuggestReportTypeUseCase via ChromaDB similarity, PATCH /reports/{id}/report-type for agent/admin, ai_source provenance field, and UX for suggestion review

DONE | 2026-06-25 19:19 UTC | STARTED | 2026-06-25 19:14 UTC | reflect | IA tools para sugerir topicos ausentes de relatos. Hoje a plataforma e os dados sinteticos assumem que todos os relatos sao existentes.  Quero pensar em como introduzir no app a opcao da IA sugerir topicos para relatos com topicos inexistentes. na tabela de dados, podemos ter colunas especiais ( com algum simbolo indicando a info gerada por IA) hoje ja temos tags. poderemos introduzir topicos também, para relatos sem topicos.

DONE | 2026-06-25 12:19 UTC | STARTED | 2026-06-25 12:15 UTC | implement | seed citizen01 test data and verify features (plan 000170) — add more user relatos and mixed-user encaminhamento | PLAN | 000170

DONE | 2026-06-25 12:09 UTC | STARTED | 2026-06-25 12:04 UTC | plan | seed citizen01@gavea.br. I want to log inas citzen01 and see my relatos and encaminhamentos. update seed scripts in order to create this test data and check the features weve implemented | PLAN | 000170
DONE | 2026-06-25 19:44 UTC | STARTED | 2026-06-25 19:36 UTC | research | como podemos arquiteturar uma solucao usando berttopic para ser usada no contexto do gavealab. queremos uma ferramenta administrativa para: a partir de um conjunto existente de relatos do sistema, fazer fine-tunning no modelo pré treinado do bert e disponibiza-lo para ser usado por uma feature do sistema para sugerir ReportType de um relato sem a informação ( esta feature ReportTYpe nullo esta sendo implementada por outro desenvolvedor). Neste research vamos focar em estruturar o pipeline de fine-tunning e visualizacao do output das informacoes, para ser visualizadas pelos admins e desenvolvedores

DONE | 2026-06-24 20:45 UTC | STARTED | 2026-06-24 20:23 UTC | implement | GET /forwardings/mine — encaminhamentos do cidadão logado. plan 000169 | PLAN | 000169

DONE | 2026-06-24 20:04 UTC | STARTED | 2026-06-24 20:00 UTC | plan | GET /forwardings/mine — endpoint auth-required que retorna os encaminhamentos com relatos do cidadão logado. source: research-000168 | PLAN | 000169

DONE | 2026-06-24 20:04 UTC | STARTED | 2026-06-24 19:43 UTC | research | como cidadao logado, como posso acessar os encaminhamentos que possuem relatos meus ???? acho que temos que criar um filtro para encaminhamentos

DONE | 2026-06-24 19:31 UTC | STARTED | 2026-06-24 19:23 UTC | plan | plan fixes | PLAN | 000167

DONE | 2026-06-24 18:37 UTC | STARTED | 2026-06-24 18:12 UTC | implement | 164 | PLAN | 164

DONE | 2026-06-24 18:07 UTC | STARTED | 2026-06-24 18:01 UTC | plan | A e B: meus relatos leva ao workspace com filtro pre-aplicado; votos visiveis na linha da tabela e passiveis de alteracao via tabela e via mapa | PLAN | 000164

STARTED | 2026-06-24 11:53 UTC | reflect | what was done in roadmap 151 and how to test it in frontend

DONE | 2026-06-24 11:54 UTC | STARTED | 2026-06-24 11:51 UTC | plan | Folowing roadmap 151 i want to run a seed script that will run all seeds existing. also i want to have a account for every possible role: admin, public agent and citzen seeded | PLAN | 000161

DONE | 2026-06-24 11:36 UTC | STARTED | 2026-06-24 11:04 UTC | implement | roadmap 151 Wave 2

DONE | 2026-06-24 00:32 UTC | STARTED | 2026-06-24 00:26 UTC | plan | --roadmap — plan the implementation of research-000150 (votes + comments + anonymization) | PLAN | 000151

DONE | 2026-06-24 00:10 UTC | STARTED | 2026-06-24 00:06 UTC | research | investigate the citizen feedback mechanism (votes + comments) AND the blueprint gaps (anonymization) before planning. notifications not needed, gps is working on web, photo upload not needed

DONE | 2026-06-23 23:58 UTC | STARTED | 2026-06-23 23:12 UTC | reflect | on last implemented features and see what is pending

DONE | 2026-06-23 21:31 UTC | STARTED | 2026-06-23 21:28 UTC | plan | populate seed of encaminhamentos based on existing api url. filter relatos and build a 50% of relatos encaminhados. | PLAN | 000148

DONE | 2026-06-22 23:41 UTC | STARTED | 2026-06-22 23:32 UTC | explain | spec-drift

DONE | 2026-06-22 21:00 UTC | STARTED | 2026-06-22 20:52 UTC | implement | roadmap-000146 all waves (Wave 0 backend 95b5085, Wave 1 cesta e9cd693, Wave 2 citizen UX f422022); each wave in fresh isolated agent context per user directive | ROADMAP | 000146

DONE | 2026-06-22 20:51 UTC | STARTED | 2026-06-22 20:02 UTC | plan | Roadmap: implement research-000145 (cesta de relatos + citizen transparency journeys) in dependency-aware waves. source: research-000145 | PLAN | 000146

DONE | 2026-06-22 19:59 UTC | STARTED | 2026-06-22 19:46 UTC | research | cesta de relatos (agent journey) + citizen transparency journeys. Anchored on reflection-000144. Basket as first-class component, set-similarity for open reports, basket-vs-SelectionBar; citizen inline relato creation + relatos/encaminhamentos read surfaces + relato-encaminhamento links (gap: forwarding endpoints agent+admin only)

DONE | 2026-06-22 19:43 UTC | STARTED | 2026-06-22 19:24 UTC | reflect | on past plans and researchers. now focus on public agent and citizen transparency journeys (citizen: login + create relato via map click + form on main page, see relatos list, see encaminhamentos list, see encaminhamentos-relatos links; agente publico: login + create/edit encaminhamentos)

DONE | 2026-06-22 12:15 UTC | STARTED | 2026-06-22 11:58 UTC | check | validate

DONE | 2026-06-22 12:05 UTC | STARTED | 2026-06-22 00:02 UTC | implement | 140 | PLAN | 000140

DONE | 2026-06-21 22:49 UTC | STARTED | 2026-06-21 22:44 UTC | plan | Phase C: NL filter parser backend (IFilterParser port + AnthropicFilterParser/OllamaFilterParser + ParseNLFilter use case + POST /nl/filter endpoint) + NL assistant UX (Section 4 input, suggestion preview zone, "Aplicar sugestão" button). From research 136. | PLAN | 000140

DONE | 2026-06-21 22:50 UTC | STARTED | 2026-06-21 22:40 UTC | plan | Phase B Saved filters backend (domain port + SQLAlchemy repo + 5 use cases + CRUD router + Alembic migration) + saved filters UX (preset bar, save popover, load dropdown). FROM research 136 | PLAN | 000139

DONE | 2026-06-21 19:58 UTC | STARTED | 2026-06-21 19:50 UTC | plan | Phase A: extended plan-000131 — four-section left panel (w-72, collapsible, preset bar + active chips + draft controls + NL assistant footer placeholder), staged draft/Apply model with loadedPresetName + draftFilterName + draft-loss guard, date presets, SPA routing fix, TableView sort + Radix Dialog full-text + pagination + score column + density toggle, MapView filter-this-area. source: research-000136 + research-000129 + plan-000131 | PLAN | 000137

DONE | 2026-06-21 19:46 UTC | STARTED | 2026-06-21 19:40 UTC | research | left panel as core UI of search engine: it show the data filtering possibilities and current active filters. An Active filter has a name and can be loaded and saved. an small, on left pannel, chat allow the user to write filter intentions. the chat sugest a filter params that the user can review and apply in current UI. The user can name and save a filter easely. also review the plans and researchers linked in this conversation in order to create a better table visualization and experience on main panel

DONE | 2026-06-21 19:32 UTC | STARTED | 2026-06-21 19:20 UTC | reflect | on last researches + implemented plans. Lets plan a UI overhaul based on newly added search features and plan user filter CRUD + NL to filter params chat on left panel + filter staging + apply status

DONE | 2026-06-21 18:57 UTC | STARTED | 2026-06-21 18:57 UTC | pending | list

DONE | 2026-06-21 18:40 UTC | STARTED | 2026-06-21 18:26 UTC | implement | 132

DONE | 2026-06-21 18:27 UTC | STARTED | 2026-06-21 18:21 UTC | research | NL to SQL in the context of this project. follow research 129, 130, plan 131/132. NL->SQL as a powerful exploration/analysis tool given full control of the DB; plan 132's fixed query-params format is not flexible/powerful enough to express the full set of SQL possibilities. What alternatives do we have?

DONE | 2026-06-21 18:17 UTC | STARTED | 2026-06-21 18:13 UTC | plan | Phase B unified POST /reports/query (multi-value filters + bbox + date range + semantic ranker + pagination, SQL-as-filter-source/Chroma-ranker) + retarget research-000129 frontend onto it; NL assistant + saved filters deferred. source: research-000130 | PLAN | 000132

DONE | 2026-06-21 17:20 UTC | STARTED | 2026-06-21 17:15 UTC | plan | Implement research-000129: staged filter + Apply button (R1/D-009), fix Tipos combobox routing bug (R2), date presets (R3), table sort + full-text (R4), map filter-this-area (R5), regression tests (R6). source: research-000129 | PLAN | 000131

DONE | 2026-06-21 17:51 UTC | STARTED | 2026-06-21 17:15 UTC | research | filter assistant: natural language to query params. this will allow more complex queryes in relatos (wich will have to be supported by api) database. this could be a potent feature allowing the user to build complex queryes and visualize then. we could also build a feature to save logged user filters (save the query filter sent to api)

DONE | 2026-06-21 17:11 UTC | STARTED | 2026-06-21 16:33 UTC | research | refine data exploration search filters in front end. citizen and public agent journeys: pending-filters apply button, temporal presets (e.g. last 15 days), Tipos combobox not populating, reports table (full text + sorting), map draw-area broken / filter-by-visible-area

DONE | 2026-06-21 15:39 UTC | STARTED | 2026-06-21 15:31 UTC | communicate | how the system work, features implemented, users and journeys. Put documentation acessible in docs with a link in root's project README.md.

DONE | 2026-06-21 15:35 UTC | STARTED | 2026-06-21 15:24 UTC | implement | 124 | PLAN | 000124

DONE | 2026-06-21 15:14 UTC | STARTED | 2026-06-21 15:11 UTC | plan | R1: CPU-only PyTorch; R2: e5-small; R3: unified embeddings registry; R4: TF-IDF topics. source: research-000122 | PLAN | 000124

DONE | 2026-06-21 15:10 UTC | STARTED | 2026-06-21 12:46 UTC | research | how to reduce memory usage. our railway app is using 2GB RAM without any active usage.

DONE | 2026-06-21 00:16 UTC | STARTED | 2026-06-21 00:13 UTC | research | é possivel, dado um relato, ter uma metrica que diz que eles possuem relatos muito parecidos, em comparacao com o resto do universo de relatos ?

DONE | 2026-06-20 23:43 UTC | STARTED | 2026-06-20 23:43 UTC | plan | implementar recomendações ALTA da research-000119: index_many() batched ao ChromaSearchClient e BulkCreateReports em chunks de 500. source: research-000119 | PLAN | 000120

DONE | 2026-06-20 23:39 UTC | STARTED | 2026-06-20 23:23 UTC | research | investigar porque o seed de relatos em csv esta demorando tanto e usando mta memoria. o servidor esta usando mais que 4GB

DONE | 2026-06-20 23:10 UTC | STARTED | 2026-06-20 23:00 UTC | plan | ERROR: UNIQUE constraint failed on users.email during database seeding | PLAN | 000118

STARTED | 2026-06-20 21:46 UTC | research | logs do railway, parece que o servidor esta reiniciando quando tenta ingerir um csv

DONE | 2026-06-20 21:05 UTC | STARTED | 2026-06-20 21:03 UTC | implement | 115 | PLAN | 000115

DONE | 2026-06-20 23:55 UTC | STARTED | 2026-06-20 23:54 UTC | plan | aplicar correções de deploy Railway: JWT_SECRET_KEY em .env.example, DATABASE_URL absoluto, /health com DB probe, remover frontend/dist/ do .dockerignore. source: research-000114 | PLAN | 000115

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
