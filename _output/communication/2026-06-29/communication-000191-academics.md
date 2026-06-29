# Communication 000191 | ACD | 2026-06-29 11:41 UTC | Academics (INF2921 professors)

> Fonte: esta comunicacao reconstroi a historia de implementacao de fala-gavea a partir dos planos marcados DONE em `_output/plans/`, dos roadmaps estrategicos, e dos research logs e reflections que motivaram cada fase. A fronteira "entregue vs. idealizado" foi auditada em `_output/research-logs/research-000185-fase5-text-vs-implementation-gap.md`. Toda afirmacao sobre o que existe esta ancorada em `product-design/project/product-design-as-coded.md`, nas decisoes D-001..D-017 de `product-design-as-intended.md`, e no codigo em `src/fala_gavea/`. Este documento e cronologico e deliberadamente distinto do roteiro de apresentacao (communication-000187), que e organizado por problema -> casos de uso -> jornadas -> features -> arquitetura.

---

## Visao geral do projeto

**fala-gavea** e um sistema de demandas de cidadaos para seguranca urbana no bairro da Gavea (Rio de Janeiro), construido para a disciplina INF2921/CIS2114 - AI Systems Design (2026.1, PUC-Rio). Equipe: Andrey, Mauro, Julia, Herbert, Natali. O cidadao registra um problema georreferenciado (localizacao, tipo, urgencia); o agente publico tria e cria um encaminhamento institucional que agrega varios relatos num unico orgao competente; e uma camada de IA assiste a exploracao da base por busca semantica e chat em linguagem natural.

**Proposta deste documento.** O artigo de apresentacao ja descreve *o que* o sistema e. Aqui o objeto e diferente: e a **trajetoria de construcao**, do primeiro commit (17/jun/2026) ao estado atual (28/jun/2026) - 383 commits, organizados pelo ciclo SEJA de pesquisa -> plano -> implementacao -> reflexao. A tese metodologica que sustenta esta comunicacao e que a propria linha do tempo e um artefato de pesquisa: cada feature entregue rastreia para tras ate um research log que a motivou e para a frente ate uma reflection que registrou o aprendizado. Para uma banca de AI Systems Design, esse encadeamento - e nao apenas o produto final - e a contribuicao academica.

**Nota terminologica (audiencia interdisciplinar).** Usamos *relato* para a demanda registrada pelo cidadao; *encaminhamento* para o ato institucional de agregar relatos e direciona-los a um orgao; *RAG* (Retrieval-Augmented Generation) para a geracao de texto condicionada a documentos recuperados; *embedding* para a representacao vetorial densa de um texto; *roadmap*, *plan*, *research log* e *reflection* sao os artefatos versionados do ciclo SEJA. *DONE* designa um plano cuja implementacao foi concluida e auditada por QA; *pending* designa um plano ainda nao implementado.

**Como ler esta linha do tempo.** Cada fase abre com a janela de datas e o roadmap estrategico que a enquadra, lista os planos DONE que a compoem, e explica em prosa a motivacao (research) e o aprendizado (reflection). Os identificadores (plan-NNNNN, research-NNNNN, reflection-NNNNN, D-NNN) sao verificaveis nos arquivos correspondentes, de modo que outro pesquisador possa reconstruir o encadeamento.

---

## Os quatro roadmaps (o eixo estrategico)

A construcao nao foi linear-ad-hoc: foi guiada por quatro roadmaps, cada um abrindo um arco de planos. Eles dao a estrutura macro sobre a qual as fases abaixo se assentam:

- **roadmap-00001** - o aplicativo nucleo de demandas de seguranca da Gavea (Fases 0, 1, 3).
- **roadmap-00002** - a "wave 2" de espacos semanticos / IA (Fase 2 e o redesenho da Fase 4).
- **roadmap-000146** - cesta de relatos e transparencia para o cidadao (Fase 5).
- **roadmap-000151** - feedback do cidadao: votos, comentarios, anonimato (Fase 5).

A IA, em todos eles, e tratada por uma decisao de projeto explicita - **D-005: IA como assistencia, nao automacao**. Essa decisao, tomada cedo, organiza todas as escolhas tecnicas que vieram depois.

---

## Fase 0 - Fundacao e arquitetura (17/jun)

**Roadmap:** roadmap-00001. **Planos DONE:** plan-00002 (scaffold + seja-setup), plan-000073 (Wave 0 item 1 - dominio, auth, reports), plan-000075 (Wave 0 item 2 - ReportType CRUD).

O projeto comecou, no mesmo 17 de junho, com tres decisoes estruturantes. A primeira (plan-00002) foi montar o esqueleto de **arquitetura limpa** em quatro camadas (domain / application / infrastructure / presentation) ja sob o harness SEJA - ou seja, a infraestrutura de pesquisa/plano/reflexao foi instalada *antes* da primeira feature. Isso e relevante metodologicamente: o registro de decisoes nasceu junto com o codigo, nao foi reconstruido depois.

A segunda (plan-000073) entregou o nucleo de dominio - entidades como dataclasses puras, autenticacao JWT com os papeis citizen/agent/admin, e a entidade `report` -, materializado em 5 tabelas SQLAlchemy, schemas Pydantic e testes de integracao. A decisao **D-003 (autenticacao JWT Bearer simples para PoC)** e a **D-001 (novo projeto independente via scaffold)** ancoram este passo.

A terceira (plan-000075) implementou o CRUD de `ReportType` com soft-delete. A escolha de modelar tipos de problema como **taxonomia dinamica em tabela**, e nao como enum hardcoded, e a **decisao D-002** - uma decisao com consequencias adiante, porque mantem a taxonomia evoluivel sem alteracao de codigo.

O resultado da Fase 0 e uma base testavel com a regra da dependencia ja imposta: tudo aponta para o dominio, e nenhuma tecnologia externa contamina as regras de negocio.

---

## Fase 1 - CRUD nucleo e o primeiro frontend (17-18/jun)

**Roadmap:** roadmap-00001. **Planos DONE:** plan-000079 (Forwarding CRUD), plan-000082 (Frontend SPA React), plan-000084 (seed de usuarios), plan-000085 (seed de relatos, 1 ano de dados).

Com o nucleo de relatos pronto, a Fase 1 fechou a outra ponta do laco: o **encaminhamento** (plan-000079). A modelagem aqui e uma escolha de projeto deliberada - **D-004: o encaminhamento e uma agregacao many-to-many de relatos**, mediada pela entidade de juncao `ForwardingReport`. Isso codifica, no esquema de dados, a intuicao central do dominio: N relatos do mesmo problema (tres mensagens sobre o mesmo poste apagado) devem virar **um** encaminhamento a RioLuz, nao tres.

O plan-000082 trocou a abordagem de frontend. O design original previa HTML estatico + Leaflet (**D-006**), mas a equipe optou por um SPA React 18 + Vite + TypeScript + Tailwind + react-leaflet - registrado como **D-007, que explicitamente supersede o D-006**. A rastreabilidade dessa virada e justamente o tipo de evidencia que o ciclo SEJA preserva: a decisao antiga nao e apagada, e marcada como superada, com a nova apontando para ela.

Os seeds (plan-000084, plan-000085) povoaram usuarios padrao e um ano de relatos sinteticos - condicao necessaria para que qualquer feature analitica subsequente tivesse dados sobre os quais operar. A **reflection-000086** registrou, ao fim desta fase, o estado do CRUD frente ao roadmap: o que estava de pe e o que ainda faltava.

---

## Fase 2 - A camada semantica e a primeira IA (19/jun)

**Roadmap:** roadmap-00002 (wave 2 - espacos semanticos / IA). **Planos DONE:** plan-000089 (infra semantica - deps, embeddings, portas, ChromaDB), plan-000090 (pipeline de ingestao + backfill), plan-000094 (busca semantica + relatos similares), plan-000099 (BERTopic), plan-000100 (chat RAG NL), plan-000104 (workspace grid + cross-filter + widgets de IA).

Esta foi a fase mais densa em termos de IA, toda condensada em 19 de junho. A sequencia e instrutiva porque segue a ordem de dependencia correta: primeiro as **portas de dominio** e a infraestrutura (plan-000089) - `ISemanticSearchPort`, `IReportIndexer`, `ILLMClient` -, depois o **pipeline de ingestao** que indexa relatos no ChromaDB com backfill do corpus existente (plan-000090), so entao os **endpoints** de busca semantica e relatos similares (plan-000094), e por fim duas camadas analiticas: modelagem de topicos com BERTopic (plan-000099) e o **chat RAG em linguagem natural** (plan-000100).

A decisao **D-005 (IA como assistencia)** se materializa aqui pela primeira vez de forma concreta: o chat RAG **cita os IDs dos relatos** usados como contexto (`cited_report_ids`), tornando cada afirmacao gerada rastreavel ate suas fontes.

O plan-000104 trouxe o primeiro frontend analitico: o **workspace em grid** com filtro a esquerda, cross-filter e widgets de IA. Mas a **reflection-000097** registrou uma tensao honesta deste momento: o *backend* semantico estava pronto, enquanto o *frontend* correspondente ainda exibia "em breve" em varios pontos. Esse descompasso backend-pronto / frontend-pendente e um padrao recorrente em desenvolvimento assistido por IA, e o fato de a equipe te-lo registrado por escrito (reflection-000097, depois reflection-000103 sobre a jornada de relatos/filtro/visualizacao de IA) e parte do valor metodologico do ciclo. A motivacao da visualizacao em grid esta documentada em research-000092.

---

## Fase 3 - Dados em escala, deploy e o pivot de memoria (19-21/jun)

**Roadmap:** roadmap-00001. **Planos DONE:** plan-000096 (Dockerfile + Railway), plan-000105 (CSV seed API + bulk insert), plan-000109 (admin seed topicos + wipe + bootstrap admin), plan-000112 (Admin Panel page), plan-000113 (seed de relatos no painel admin), plan-000115 (Railway deploy fixes), plan-000118 (fix race de email duplicado), plan-000120 (batch indexing), plan-000124 (reducao de memoria Railway).

Tendo features, a Fase 3 enfrentou a realidade de coloca-las em producao. O empacotamento foi um Dockerfile multi-stage (build do SPA em node, runtime em python:3.13-slim) com deploy na Railway (plan-000096, com fixes em plan-000115), motivado pelas pesquisas research-000091 (host publico via docker) e research-000114 (stack de deploy do frontend). Em paralelo, a operacao de dados amadureceu: endpoint de seed por CSV e bulk insert (plan-000105, motivado por research-000119 sobre performance de seed CSV), o **painel admin** para seed/wipe/bootstrap (plan-000109, plan-000112, plan-000113, com research-000110 sobre as operacoes de admin no frontend), e a indexacao em lote (plan-000120).

O momento mais interessante desta fase, do ponto de vista de engenharia de sistemas de IA, e o **pivot de memoria** (plan-000124, motivado por research-000122). O ambiente de producao da Railway impunha um teto de memoria incompativel com a stack de IA original. A equipe tomou tres decisoes acopladas: trocar torch-GPU por **torch-CPU**, adotar o modelo de embedding leve **e5-small** (`intfloat/multilingual-e5-small`), e **substituir BERTopic por TF-IDF + K-means** para a extracao de topicos. O BERTopic, embora instalado em plan-000099, permaneceu dormente.

Este episodio e a arquitetura limpa pagando dividendos sob restricao real: porque a IA vive atras de portas com injecao de dependencias, a reconfiguracao da stack ocorreu sem tocar no nucleo de casos de uso. A separacao entre regra de negocio e tecnologia deixou de ser argumento de design e virou alavanca pratica. A pesquisa research-000121 (metrica de similaridade relativa ao corpus) tambem alimentou esta fase, refinando como o ranqueamento semantico se comporta.

---

## Fase 4 - O redesenho da exploracao de dados (21/jun)

**Roadmap:** roadmap-00002. **Plano-pai (REDESIGN):** plan-000131. **Planos DONE:** plan-000132 (API unificada de consulta - Phase B), plan-000137 (Phase A - painel estendido, draft filters, table UX), plan-000139 (Phase B - saved filters), plan-000140 (Phase C - parser NL -> filtro + NL assistant UX).

A Fase 4 foi um redesenho deliberado, nao uma adicao incremental. A pesquisa que o motivou e densa e vale citar por inteiro: research-000129 (search filters), research-000130 (NL -> query params), research-000133 (NL -> SQL) e research-000136 (left panel search engine + NL chat) exploraram quatro abordagens para tornar a exploracao de dados mais poderosa. A **reflection-000134** consolidou o overhaul da UI - filtros de busca e o painel de chat NL.

O resultado tem tres camadas. Primeiro, uma **API unificada de consulta** (`POST /reports/query`, plan-000132): filtros multivalor + ranqueamento semantico + paginacao, com o padrao-chave de que o **SQL filtra e o ChromaDB so ranqueia**. Segundo, a UX de exploracao (plan-000137, plan-000139): filtro encenado (rascunho + "Aplicar"), chips de filtro ativo e presets de filtro salvos via entidade `SavedFilter`. A escolha do filtro encenado sobre o cross-filtering ao vivo e a **decisao D-009**, que por sua vez ajustou a **D-008** (workspace em grid de ferramentas).

Terceiro, e mais relevante para a tese de IA-como-assistencia, o **parser NL -> filtro** (plan-000140): o agente descreve a intencao em linguagem natural e o sistema *propoe* um filtro - **mas nunca auto-aplica**; o usuario precisa clicar "Aplicar sugestao ao rascunho". As dimensoes traduziveis foram deliberadamente limitadas (tipo, urgencia, status, janela temporal, texto), sem dimensao geografica - uma restricao consciente. Note-se que a abordagem NL -> SQL pesquisada em research-000133 *nao* foi a escolhida; a equipe optou por NL -> parametros de consulta estruturados, mais seguros e auditaveis. Essa escolha entre alternativas pesquisadas e exatamente o tipo de decisao que o ciclo SEJA torna visivel.

---

## Fase 5 - Transparencia e feedback do cidadao (23-24/jun)

**Roadmaps:** roadmap-000146 (cesta de relatos / transparencia) + roadmap-000151 (feedback do cidadao). **Planos DONE:** plan-000148 (seed encaminhamentos), plan-000152 (schema - votes, comments, anon tokens, author_id nullable), plan-000153/000154/000155 (backends de votos / comentarios / relato anonimo), plan-000156/000157/000158 (UX correspondentes), plan-000161 (seed runner + contas por papel), plan-000164 (Meus relatos + votos inline), plan-000167 (performance - warm-up, singleton thread-safe, indice de DB), plan-000169 (GET /forwardings/mine), plan-000170 (seed de dados de teste do citizen01).

A Fase 5 voltou o foco para o cidadao, fechando a terceira ponta do laco: a **transparencia**. A pesquisa research-000145 desenhou as jornadas de cesta de relatos e transparencia, e research-000150 desenhou o feedback civico (votos, comentarios, anonimizacao). A sequencia exemplar foi schema -> backend -> UX, fase a fase: primeiro o esquema de dados (plan-000152, que tornou `author_id` nullable para suportar relato anonimo), depois os tres backends, so entao as tres UX.

As decisoes de projeto desta fase sao numerosas e finas: **D-010** ("relato aberto" = somente status `pendente`), **D-011** (leitura de encaminhamentos e publica, sem login), **D-012** (lista de relatos do cidadao = todos + filtro "meus relatos"), e **D-013** (a "cesta de relatos" eleva `selectedIds` e substitui a SelectionBar flutuante). O relato anonimo usa coordenadas arredondadas (para reduzir reidentificacao) mais um token de reivindicacao unico.

As reflections desta fase documentam o gap entre jornada projetada e implementada: reflection-000144 (jornadas de transparencia), reflection-000149 (blueprint das jornadas do cidadao + feedback) e reflection-000163 (gaps de frontend do roadmap-151 - votos, meus-relatos). O plan-000164 fechou parte desses gaps (votos inline em tabela e mapa, ordenacao, fix da API de voto), e o plan-000169 entregou os encaminhamentos do proprio cidadao (research-000168). O plan-000167 cuidou de performance - warm-up no startup, singleton thread-safe e indice de DB -, um passo de maturidade que so faz sentido depois que ha features suficientes para que a latencia importe.

---

## Fase 6 - Proveniencia de IA e o assistente da plataforma (25-26/jun)

**Planos DONE:** plan-000177 (chat helper da plataforma - RAG self-docs - POST /nl/help), plan-000178 (AiBadge - marcador de proveniencia de IA), plan-000181 (embed da metodologia SEJA no helper - D-017), plan-000183 (pipeline de seed showcase).

A Fase 6 e a fase mais "meta" do projeto, e a mais relevante para uma disciplina de AI Systems Design, porque trata da **comunicabilidade da IA** - como o sistema sinaliza ao usuario o que e gerado e de onde veio. Tres entregas a compoem.

Primeiro, o **helper da plataforma** (plan-000177, motivado por research-000175): um *segundo* chat RAG, distinto do chat de relatos, que responde perguntas sobre como a propria plataforma funciona, a partir da documentacao do projeto indexada numa colecao Chroma de self-docs, com filtro de visibilidade por papel. A decisao de mante-lo como **bounded context separado** do chat de relatos e a **D-014**. O plan-000181 (research-000180) embutiu o enquadramento da metodologia SEJA no prompt do helper para a audiencia admin - resolvido como **D-017** (o helper como "deputy de proveniencia honesta", com framing meta por papel).

Segundo, o **AiBadge** (plan-000178, motivado por research-000176): um marcador reutilizavel de proveniencia de IA, visivel em toda a interface onde a IA atua. A unificacao desse marcador e a **decisao D-015**. E uma escolha de comunicabilidade no sentido proprio da engenharia semiotica: o badge e parte da mensagem de metacomunicacao que o designer enderaca ao usuario, demarcando a fronteira entre conteudo humano e gerado.

Terceiro, o pipeline de seed showcase local (plan-000183).

### Trabalho planejado, nao entregue (a hipotese de design central)

E aqui que a honestidade metodologica e mais importante. Duas capacidades foram **pesquisadas e planejadas, mas continuam pending - nao foram implementadas**:

- **Sugestao de tipo de relato por IA** (plan-000174, ainda pending). A pesquisa registrou *duas* abordagens concorrentes: research-000170/000172 sobre classificacao com DistilBERT supervisionado, e a alternativa de similaridade via ChromaDB. A **reflection-000173** documentou explicitamente essa tensao de design (DistilBERT supervisionado vs. ChromaDB por similaridade), e a **reflection-000171** havia levantado o problema de relatos sem topico. A decisao registrada (D-002, taxonomia dinamica) torna o problema interessante: se os tipos sao dinamicos, um classificador supervisionado precisa lidar com classes que mudam.
- **Sintese de comentarios de encaminhamento** (plan-000179, ainda pending; **decisao D-016**): uma sintese agent-only, efemera e on-demand dos comentarios de um encaminhamento.

Apresentar essas capacidades como entregues seria impreciso. Elas sao a **hipotese de design** central que a base entregue habilita: sugestao de categoria por IA -> correcao pelo agente -> evento de curadoria -> realimentacao few-shot. Nenhum desses elementos existe no codigo hoje (nao ha categorizacao automatica, nao ha `PATCH /reports/{id}` para correcao, nao ha entidade de "evento de curadoria", nao ha loop de few-shot). Apresenta-los como direcao futura testavel e a postura correta.

---

## Fase 7 - Polimento e prontidao para a demo (26-28/jun)

**Planos DONE:** plan-000183 (seed showcase local, transicional com a Fase 6), plan-000189 (clusterizacao de coordenadas em POIs reais da Gavea).

A fase final tratou de prontidao para demonstracao. O plan-000189 reescreveu as coordenadas dos relatos sinteticos para clusteriza-las em pontos de interesse reais da Gavea (Rocinha, PUC, Parque da Cidade, Baixo Gavea), com fonte unica e determinismo - evitando que pontos "vazassem" para Jardim Botanico/Lagoa e tornando a demo geograficamente plausivel. A research-000190 motivou o ultimo refinamento de UX: linkar o relato selecionado no mapa com a tabela.

Vale registrar duas pesquisas reflexivas desta janela final, porque sao o que distingue o projeto. A research-000188 fez triagem de arquivos nao commitados (higiene de repositorio), e - mais importante - a **research-000185** conduziu uma auditoria honesta do gap entre o texto (o que se diz que o sistema faz) e a implementacao (o que ele de fato faz), enquanto research-000186 preparou o discurso para os professores. A separacao entregue vs. idealizado que permeia esta comunicacao vem diretamente dessas duas pesquisas. A research-000147, mais cedo, ja havia tratado de spec-drift - a deriva entre intencao e codigo -, um cuidado que o ciclo SEJA institucionaliza.

---

## Metodologia como artefato: a contribuicao academica

A linha do tempo acima nao e apenas um relato de progresso; e a **evidencia material do ciclo SEJA** (research -> plan -> implement -> reflect) operando sobre um projeto real de desenvolvimento assistido por IA. Tres propriedades a tornam relevante para INF2921:

1. **Rastreabilidade bidirecional.** Cada feature entregue tem um antecedente (um research log que a motivou) e um consequente (uma reflection que registrou o aprendizado). As 26 pesquisas e 11 reflexoes catalogadas nao sao subproduto - sao o registro da deliberacao de design. Outro pesquisador pode reconstruir *por que* cada escolha foi feita, nao apenas *o que* foi construido.

2. **Decisoes como objetos de primeira classe.** As 17 decisoes D-001..D-017 formam um namespace estavel de decisoes de design no estilo DRR (decision, rationale, consequences). Decisoes superadas nao sao apagadas (D-006 -> D-007; D-008 -> D-009): a evolucao do pensamento de projeto fica preservada, o que e raro em projetos de curso e essencial para estudo metodologico.

3. **Separacao as-intended / as-coded.** O projeto mantem, deliberadamente, dois registros distintos: o que se *pretendeu* (`product-design-as-intended.md`) e o que se *codificou* (`product-design-as-coded.md`). Essa separacao e o que torna possivel a auditoria honesta de gap (research-000185) e a deteccao de spec-drift (research-000147). E o mecanismo que sustenta a subsecao seguinte.

O argumento para a banca e este: fazer design de sistema de IA *com* assistencia de IA, mantendo rastreabilidade completa de decisao, e exatamente o objeto de estudo da disciplina. fala-gavea e simultaneamente o produto e o caso de estudo.

---

## Entregue vs. idealizado (consolidacao honesta)

Para fechar com a precisao que uma banca de AI Systems Design exige, segue a fronteira consolidada entre o que esta no ar e o que e hipotese.

**Entregue e verificavel no codigo (camada de IA):**

- Busca semantica de relatos (`GET /reports/search`) e relatos similares (`GET /reports/{id}/similar`, `POST /reports/similar-to-set`).
- Chat RAG sobre relatos (`POST /nl/chat`) com citacao de IDs de fonte (`cited_report_ids`).
- Parser NL -> filtro (`POST /nl/filter`) que *propoe* mas nunca auto-aplica.
- Palavras-chave por TF-IDF + K-means (`GET /reports/keywords`).
- Helper da plataforma por RAG sobre self-docs (`POST /nl/help`) com filtro de visibilidade por papel.
- Marcador de proveniencia de IA (`AiBadge`) na interface.

**Idealizado / planejado, NAO entregue (hipotese de design):**

- Sugestao de tipo de relato por IA (plan-000174, pending; tensao DistilBERT vs. ChromaDB em reflection-000173).
- Correcao de categoria pelo agente como evento de curadoria (sem `PATCH /reports/{id}`, sem entidade de evento de curadoria).
- Sintese de comentarios de encaminhamento (plan-000179, pending; D-016).
- Loop de aprendizado por few-shot que realimenta correcoes humanas (inexistente; BERTopic instalado porem dormente).

A distincao nao e uma ressalva defensiva - e a delimitacao precisa do que foi construido neste ciclo e do que constitui a agenda de pesquisa natural a partir desta base. O humano permanece no comando da curadoria; a IA assiste, cita suas fontes, e nunca decide sozinha. Essa e, ao mesmo tempo, a tese de projeto e o resultado verificavel da trajetoria narrada acima.
