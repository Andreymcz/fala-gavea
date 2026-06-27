# Communication 000184 | ACD | 2026-06-26 22:27 UTC | Academicos

> Fonte: material-fonte curado de linha do tempo e moldura de design (`fala-gavea-timeline-source.md`), verificado e enriquecido contra `product-design/project/product-design-as-coded.md` (## Conceptual Design, ## Metacommunication, ## Journey Maps), `product-design-as-intended.md` (Decisoes D-001..D-017) e `constitution.md`.

Material de referencia e explicacao, redigido para ser citado e adaptado diretamente em um relatorio academico final (INF2921/CIS2114 - AI Systems Design, PUC-Rio, 2026.1). O conteudo trata do sistema **fala-gavea** e de seu processo de design e implementacao como artefato de pesquisa em Engenharia Semiotica.

---

## 1. Visao geral do projeto

### Identidade e missao

O **fala-gavea** e um sistema de demandas cidadas para seguranca urbana no bairro da Gavea (Rio de Janeiro), construido como prova de conceito para a disciplina INF2921/CIS2114 - AI Systems Design (PUC-Rio, 2026.1). Equipe: Andrey, Mauro, Julia, Herbert, Natali.

O sistema articula tres papeis em torno de um fluxo unico de tratamento de demandas urbanas:

- **Cidadao** registra um problema urbano com localizacao GPS, tipo, urgencia e texto livre (e, opcionalmente, foto e modo anonimo).
- **Agente publico** explora as demandas - filtra, agrupa relatos similares, le padroes - e cria encaminhamentos formais para orgaos responsaveis (RioLuz, COMLURB e congeneres).
- **Administrador** mantem dinamicamente a taxonomia de tipos de problema.

### Fase atual

O projeto encontra-se em **estagio de polimento**: a plataforma nuclear, a camada semantica de IA, o workspace de exploracao, a transparencia cidada e o feedback cidadao estao entregues e funcionando ponta-a-ponta; a fronteira ativa concentra-se em features recentes de proveniencia de IA e no fechamento da lacuna entre intencao de design e implementacao (Secao 4). A janela de desenvolvimento foi de 2026-06-17 (primeiro commit) a 2026-06-26 - cerca de dez dias, 345 commits, 4 roadmaps, 45 planos, 22 ciclos de pesquisa, 11 reflexoes e 17 decisoes de design registradas (D-001..D-017).

### Proposta de valor e diferenciais

O problema que o sistema endereça e a fricao entre a demanda cidada dispersa e a acao publica coordenada: como transformar um volume alto de relatos heterogeneos em encaminhamentos informados sem que a decisao publica seja terceirizada para uma maquina. Quatro diferenciais sustentam a resposta:

- **IA como assistencia, nunca como decisao.** Busca semantica, relatos similares e chat em linguagem natural ajudam o agente a entender padroes; a decisao de encaminhar - para qual orgao, com qual solucao proposta - e sempre humana. Esse e o invariante central de design, atravessando D-005, D-015 e D-017.
- **Privacidade local-first.** Por padrao toda inferencia LLM roda localmente via Ollama; os dados cidadaos nao saem da maquina. Isto e um requisito constitucional (principio C1) e nao apenas uma configuracao: `FALA_GAVEA_LLM_PROVIDER=ollama` mantem o texto dos relatos local; o banco `fala_gavea.db` e versionado-fora (gitignored, invariantes S2/T4).
- **Tipos de problema dinamicos.** A taxonomia de relatos e gerida em tabela (CRUD administrativo, soft-delete), nao codificada como enum - o vocabulario do dominio permanece mutavel sem mudanca de codigo.
- **Transparencia cidada.** Leituras publicas de encaminhamentos (sem expor o agente responsavel), visao "Meus relatos" e proveniencia de IA explicita tornam o circuito demanda->encaminhamento auditavel pelo proprio cidadao.

---

## 2. Fundamentacao teorica (Engenharia Semiotica)

O fala-gavea pode ser lido como uma operacionalizacao da **Engenharia Semiotica** de Clarisse de Souza, em que a interface e tratada como uma mensagem unidirecional do designer ao usuario - uma metacomunicacao em que o designer diz, em substancia: "este e o sistema que projetei, para voce, para estes fins, e e assim que voce interage com ele". O projeto e particularmente interessante para a tradicao porque insere um terceiro agente - a IA - no canal designer-usuario, e tematiza explicitamente como a IA deve se comunicar para nao corromper essa mensagem.

### A mensagem de metacomunicacao do designer

A mensagem que o fala-gavea emite e estavel entre os tres papeis: "eu, designer, projetei isto para voce - cidadao, agente, administrador - e a IA esta aqui para te ajudar a explorar, nao para decidir por voce". Essa mensagem nao e implicita: ela esta **codificada nos documentos de design-intent** (a visao de metacomunicacao e as intencoes por feature em `product-design-as-intended.md`) antes de estar materializada na interface. O log de metacomunicacao por feature do as-coded torna isso explicito; para o Workspace Grid (plan-000104), a intencao registrada do designer e:

> "Eu te dou um workspace onde *voce* decide como ler os relatos - o filtro e seu e singular, e cada visao (mapa, tabela, topicos, similares, chat) olha o mesmo conjunto por angulos diferentes. A IA aparece como apenas mais uma lente de exploracao, sempre citando de onde tirou suas respostas - assistencia, nao decisao."

Os documentos de design-intent funcionam, assim, como o **template de metacomunicacao do designer**: o lugar onde a "fala" do designer e redigida e revisada antes de ser emitida pela interface.

### Comunicabilidade da IA como assistencia

A categoria de **comunicabilidade** - a capacidade da interface de comunicar ao usuario a logica de design pretendida - manifesta-se aqui como um conjunto de **signos metalinguisticos**: a interface fala sobre sua propria IA. Cada decisao concreta abaixo sustenta a mensagem de que a IA assiste mas nao decide:

- **Citacoes de proveniencia.** O chat RAG sobre relatos (`POST /nl/chat`) retorna `cited_report_ids`; o helper da plataforma (`POST /nl/help`) retorna `cited_docs`, renderizados como lista "Fontes". A IA mostra de onde tirou a resposta, em vez de afirma-la sem origem.
- **Marcador de proveniencia (AiBadge, D-015).** Conteudo gerado por IA e marcado como tal - sinalizando "pode conter erros, revise antes de agir". (Planejado; ver Secao 4 quanto ao status de implementacao.)
- **Nunca-auto-aplica.** A sugestao de tipo de relato nunca e aplicada automaticamente; o filtro em linguagem natural (`POST /nl/filter`) produz um rascunho de filtro que so toma efeito quando o usuario clica "Aplicar" (filtro encenado, D-009). A acao decisoria permanece um ato humano explicito.

Esses signos sao a forma pela qual a comunicabilidade e preservada apesar da mediacao da IA: a IA nunca se apresenta como autoridade, e sim como uma lente cuja origem e sempre exibida.

### O helper como deputy de proveniencia honesta (D-017)

O assistente de ajuda da plataforma (`POST /nl/help`, plan-000177) e um **caso de dogfooding semiotico**: o sistema explica a si mesmo a partir do seu proprio corpus de documentacao de design, indexado em uma colecao Chroma separada (`falagavea_selfdocs`). Ele se apresenta como divulgacao honesta de proveniencia - "minha base e a documentacao de design do projeto e eu sempre cito as fontes" - sem alegacoes antropomorficas. Na terminologia da Engenharia Semiotica, o helper atua como **deputy** (preposto) do designer: ele estende a fala do designer ao usuario em tempo de execucao, e D-017 embute a propria metodologia do projeto no prompt do helper, de modo que a divulgacao de proveniencia seja honesta por papel (a visibilidade dos trechos respeita citizen/agent=public, admin=public+internal, com negacao por padrao).

---

## 3. Arquitetura como artefato de pesquisa

A arquitetura do fala-gavea e relevante para a pesquisa nao apenas pelo que constroi, mas pelo que **torna visivel**.

### Arquitetura limpa e o construto da fala unica do designer

O sistema adota arquitetura limpa em quatro camadas - `domain` (entidades como dataclasses puras, portas como ABCs), `application` (casos de uso, sem acesso direto a banco ou HTTP), `infrastructure` (SQLAlchemy, ChromaClient, OllamaClient/AnthropicClient) e `presentation` (routers FastAPI, schemas Pydantic). Duas convencoes constitucionais sao semioticamente carregadas: **toda chamada LLM e busca semantica passa por `infrastructure/`** (T1) e **nenhum router acessa JWT diretamente** (T2). O efeito e que a "voz" da IA e a "voz" da autorizacao tem, cada uma, um unico ponto de emissao auditavel - substituir o provedor de LLM ou o esquema de autenticacao e uma mudanca localizada, e a mensagem que o sistema emite ao usuario nao se fragmenta em vozes inconsistentes espalhadas pelo codigo.

### As-intended vs as-coded como mecanismo de visibilidade de spec-drift

A contribuicao metodologica mais citavel do projeto e a **separacao explicita entre intencao (as-intended) e implementacao (as-coded)**. O design-intent - mantido por humanos via marcadores - registra o que foi projetado; o as-coded - mantido pelo agente - registra o que foi efetivamente construido. A distancia entre os dois (a deriva de design, ou *spec-drift*) torna-se um objeto observavel e auditavel, e nao um residuo tacito. O registro de jornadas ilustra: as jornadas projetadas JM-TB-001 (registro), JM-TB-002 (encaminhamento) e JM-TB-003 (exploracao/analise no workspace por multiplas visoes) constam como implementadas ponta-a-ponta no as-coded, com a delta "Differs from Intent" explicitamente vazia - uma afirmacao verificavel, nao uma suposicao.

### Decisoes de design (D-NNN) como registro auditavel

As 17 decisoes de design (D-001..D-017) formam um registro estavel e enderecavel que mapeia escolhas estruturais a construtos semioticos. Exemplos: D-007 (supersede D-006) substitui o frontend HTML estatico por uma SPA React+Vite+TS; D-008 substitui o modelo map-centric por um workspace em grid com visoes intercambiaveis sobre um filtro unico; D-009 introduz o filtro encenado (rascunho + "Aplicar"); D-010..D-013 fecham a transparencia cidada; D-014 introduz o helper auto-documentado; D-015 o marcador de proveniencia; D-017 embute a metodologia no prompt do helper. Cada D-NNN e simultaneamente um registro de engenharia (o que mudou e por que) e um registro semiotico (como a mudanca afeta a mensagem do designer ao usuario). Esse cruzamento - decisao tecnica reversivel ancorada a uma justificativa de metacomunicacao - e o que confere ao processo carater de artefato de pesquisa.

---

## 4. Linha do tempo do projeto (intencao -> entrega)

O desenvolvimento organizou-se em cinco epocas. Cada epoca parte da intencao de um roadmap, desce a planos, e converge (ou nao) em entrega. A leitura intencao->entrega abaixo e a espinha factual para a secao de processo do relatorio.

| Epoca | Janela | Intencao do roadmap | Entregue | Pivos e lacunas |
|-------|--------|---------------------|----------|------------------|
| **1 - Plataforma nuclear** (roadmap-00001) | 17-18/jun | Cidadao registra relato -> agente encaminha -> IA assiste; D-A..D-F | Scaffold FastAPI + arquitetura limpa (plan-00002); 5 entidades de dominio + auth JWT + reports (plan-000073); CRUD admin de ReportType com soft-delete e seed de 8 tipos (plan-000075); CRUD de Forwarding many-to-many com cascata de status (plan-000079); seed de usuarios + 10k relatos por 1 ano (plan-000084/085) | **PIVO D-006->D-007** (plan-000082): a intencao era HTML estatico + Alpine + Leaflet; virou SPA React+Vite+TS por feedback do usuario ("visual mais fluido e moderno") |
| **2 - Espacos semanticos / IA** (roadmap-00002) | 18-19/jun | Espacos de embedding por proposito, hook de ingestao, BERTopic, RAG | Registry de embeddings + ChromaClient + portas de dominio (plan-000089); hook de indexacao no CreateReport + backfill dos 10k (plan-000090); busca e similares (plan-000094); chat RAG plugavel Ollama/Anthropic (plan-000100) | **CONSTRUIR-E-ESTACIONAR**: BERTopic (plan-000099) foi implementado e depois aposentado em favor de TF-IDF (plan-000124); o pacote permanece instalado, dormente, reservado para fine-tuning futuro |
| **3 - Workspace + deploy + transparencia** (roadmap-000146) | 19-23/jun | Remodelar a UI; fechar a transparencia cidada; D-008..D-013 | **PIVO map-centric -> D-008** workspace em grid (store Zustand, visoes intercambiaveis, plan-000104); deploy Docker/Railway, import CSV em massa, painel admin seed/wipe (plan-000096/105/109/112/113/115/120); clusters TF-IDF (plan-000124); endpoint unificado `POST /reports/query` (plan-000132); filtro encenado D-009 (plan-000137); presets de filtro (plan-000139); parser NL->filtro (plan-000140); transparencia cidada D-010..D-013, 3 waves no mesmo dia (roadmap-000146); seed de encaminhamentos (plan-000148) | Entrega ampla; transparencia executada em contextos isolados no mesmo dia |
| **4 - Feedback cidadao** (roadmap-000151) | 23-25/jun | Votos + comentarios + anonimizacao | Migracoes Alembic + backends de votos/comentarios/anonimato (plan-000152-155); UX correspondente (plan-000156-158); seed runner, nav "Meus relatos", `GET /forwardings/mine` (plan-000161/164/167/169); dados de teste citizen01 (plan-000170) | Execucao limpa em 3 waves |
| **5 - Features de IA mais recentes** (fronteira) | 25-26/jun | Proveniencia de IA, helper auto-documentado, dogfooding | Helper da plataforma com RAG sobre a propria documentacao, `POST /nl/help` (D-014, plan-000177, **ENTREGUE**); metodologia embutida no prompt do helper (D-017, plan-000181, **ENTREGUE**) | **A LACUNA**: tres planos planejados-nao-implementados - sugestao plugavel de tipo Chroma+DistilBERT (plan-000174); AiBadge (D-015, plan-000178); sintese de comentarios de encaminhamento (D-016, plan-000179, so agente, efemera) |

### Leituras do processo

- **Dois pivos deliberados.** D-006->D-007 (HTML estatico -> SPA, dia 2) e map-centric -> D-008 (workspace em grid, dia 3) superaram decisoes anteriores do roadmap por feedback do usuario, nao por falha de execucao. Sao casos de revisao de intencao registrada.
- **Um caso construir-e-estacionar.** BERTopic foi construido, aposentado e mantido dormente - um exemplo de decisao reversivel deixada explicita no registro, em vez de removida silenciosamente.
- **Roadmaps mais apertados ao longo do tempo.** Os primeiros roadmaps eram amplos e multi-wave, com marcadores plan-TBD; os ultimos foram execucoes no mesmo dia com planos reservados inline - uma maturacao do metodo de planejamento.
- **A fronteira e a lacuna as-intended vs as-coded.** Os tres planos nao construidos carregam as decisoes D-015 e D-016; o projeto entrou em estagio de polimento precisamente para fechar esse delta de documentacao. Aqui a intencao ultrapassa a entrega, e a metodologia torna esse excesso visivel em vez de oculta-lo.

---

## 5. Agenda de pesquisa / questoes em aberto

O fala-gavea, por inserir uma IA mediadora no canal designer-usuario e tematizar sua comunicabilidade, levanta um conjunto de questoes que excedem o escopo da prova de conceito e que servem de agenda para investigacao futura.

- **Efeito da metacomunicacao estruturada da IA sobre a confianca e a decisao do agente.** O sistema sustenta, por design, que citacoes de proveniencia (`cited_report_ids`, `cited_docs`), marcacao de conteudo gerado e o padrao nunca-auto-aplica preservam a agencia humana. Resta empiricamente em aberto se esses signos metalinguisticos de fato calibram a confianca do agente publico - se reduzem a delegacao indevida a maquina sem reduzir a utilidade da assistencia. Um estudo de comunicabilidade com agentes reais (protocolos de interpretacao de signos) seria o caminho natural.

- **Comunicabilidade quando a IA medeia a relacao designer-usuario.** A Engenharia Semiotica classica modela um canal designer->usuario. Aqui ha um deputy de execucao (a IA) que reformula a mensagem do designer em tempo real, a partir de um corpus. Em que condicoes a fala do deputy permanece fiel a fala do designer? O caso do helper auto-documentado (D-017) oferece um banco de testes concreto: o que acontece com a comunicabilidade quando o sistema explica a si mesmo a partir de seu proprio corpus de design.

- **Onde o modelo "IA-como-assistencia" se rompe.** O invariante "a IA assiste, nunca decide" e nitido no design, mas suas bordas sao questoes de pesquisa: filtros NL pre-preenchidos, sugestoes de tipo e sinteses podem, na pratica, ancorar a decisao humana mesmo sem se auto-aplicarem (efeito de anchoring). Mapear os pontos em que a assistencia se converte de fato em decisao implicita e uma questao em aberto de design de IA.

- **Avaliacao da sugestao automatica de tipo (DistilBERT vs Chroma), ainda nao construida.** O plan-000174 previa uma sugestao plugavel de tipo de relato comparando uma abordagem por embeddings (Chroma) e uma por classificador (DistilBERT). Como o plano nao foi implementado, a comparacao permanece uma questao em aberto: qual abordagem oferece melhor precisao no dominio de seguranca urbana pt-BR, e como a escolha interage com a exigencia de que a sugestao nunca seja auto-aplicada.

---

*Personas de referencia: R-P-001 Cidadao (mobile, in loco; jornada JM-TB-001); R-P-002 Agente publico (desktop, plantao; JM-TB-002, JM-TB-003); R-P-003 Administrador (manutencao da taxonomia de tipos). As tres jornadas projetadas estao implementadas ponta-a-ponta no estado as-coded.*
