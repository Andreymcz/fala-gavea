# DESIGN INTENT — fala-gavea

<!-- maintained-by: human (designer); Human (markers) classification since SEJA 2.8.3 -->

---

## 0. Planned Changes

| Target Version | Change Summary | Motivation / Rationale |
|---|---|---|
| v1 | Sistema base: cidadao registra relato, agente cria encaminhamento, IA assiste exploracao | Caso de uso core do roadmap-000071 |

---

## 1. Platform Purpose

fala-gavea é um sistema de demandas cidadãs para segurança urbana no bairro da Gávea (Rio de Janeiro). A plataforma permite que cidadãos registrem problemas de segurança e infraestrutura urbana informando localização GPS, tipo de problema, nível de urgência e uma descrição textual. Agentes públicos utilizam a plataforma para explorar as demandas registradas, identificar padrões e criar encaminhamentos formais para os órgãos responsáveis.

O sistema é projetado como prova de conceito para o curso INF2921/CIS2114 (AI Systems Design, PUC-Rio, 2026.1), demonstrando como IA pode assistir processos de gestão urbana participativa sem automatizá-los completamente. A inteligência artificial auxilia o agente público na exploração de dados (busca semântica, relatos similares, chat NL), mas a decisão de criar encaminhamentos permanece sob controle humano.

### Design Philosophy

Cidadania participativa mediada por tecnologia: a plataforma não substitui o julgamento humano — cidadãos descrevem problemas em linguagem natural e geolocalização, agentes públicos tomam decisões informadas por IA, e administradores configuram o sistema para refletir a realidade local (tipos de problema dinâmicos).

---

## 2. Entity Hierarchy

```
User
├── Report (author_id FK)
│   └── ReportType (report_type_id FK)
└── Forwarding (agent_id FK)
    └── ForwardingReport (join: forwarding_id, report_id)
        └── Report

ReportType (gerenciado pelo admin)
```

<!-- REQ-ENT-001 -->
### User

- Representa qualquer pessoa autenticada no sistema.
- Roles: `citizen` (registra relatos), `agent` (cria encaminhamentos), `admin` (CRUD de tipos de problema e gestão do sistema).
- Campos: `id` (UUID), `email` (único), `password_hash`, `name`, `role: Enum[citizen|agent|admin]`, `created_at`.
- Autenticação via JWT Bearer. Registro aberto via POST /auth/register (qualquer pessoa pode se registrar como cidadão; promoção a agent/admin é manual).
- Sem soft delete — usuários não são removidos no PoC.

<!-- REQ-ENT-002 -->
### ReportType

- Tipo de problema urbano, gerenciado dinamicamente pelo admin.
- Permite que o administrador adicione novos tipos (ex: "drenos entupidos") sem redeployar o código.
- Campos: `id` (UUID), `name` (ex: "Iluminação pública"), `description` (opcional), `active` (bool — soft delete), `created_at`.
- Visível publicamente (GET /report_types sem auth) para que cidadãos possam selecionar o tipo no formulário.
- DELETE é soft delete (active=False); tipos inativos não aparecem no formulário do cidadão.

<!-- REQ-ENT-003 -->
### Report

- Demanda do cidadão: descreve um problema urbano com localização, tipo e urgência.
- Campos: `id` (UUID), `text` (descrição), `lat: float`, `lon: float`, `urgency: Enum[alta|media|baixa]`, `photo_url: str|None` (URL livre; upload é future work), `report_type_id` FK, `author_id` FK, `status: Enum[pendente|em_analise|encaminhado|resolvido]`, `created_at`.
- Visibilidade: lista pública via GET /reports/geojson (sem auth); detalhe individual requer auth.
- Status transita: `pendente` → `em_analise` → `encaminhado` (quando incluído em Forwarding) → `resolvido`.
- Sem hard delete — relatos são permanentes para fins de auditoria cívica.

<!-- REQ-ENT-004 -->
### Forwarding

- Encaminhamento criado pelo agente público agrupando N relatos similares/relacionados e direcionando-os para um órgão responsável.
- Campos: `id` (UUID), `institution` (nome do órgão, ex: "RioLuz", "COMLURB"), `proposed_solution` (descrição da solução proposta), `status: Enum[aguardando_solucao|solucao_em_andamento|finalizado]`, `agent_id` FK, `created_at`, `updated_at`.
- Um Forwarding pode agregar múltiplos Reports (many-to-many via ForwardingReport).
- Ao criar um Forwarding, todos os Reports incluídos transitam para status `encaminhado`.

<!-- REQ-ENT-005 -->
### ForwardingReport

- Tabela de junção many-to-many entre Forwarding e Report.
- Campos: `forwarding_id` FK, `report_id` FK.
- Um Report pode estar em múltiplos Forwardings (ex: problema recorrente que gerou encaminhamentos em épocas diferentes).

---

## 3. Domain-Specific Concepts

### Tipos de Problema Dinâmicos

Os tipos de problema (ReportType) são gerenciados pelo administrador em tempo de execução, sem necessidade de redeploy. Isso reflete a realidade de gestões municipais onde categorias de demanda evoluem. Os 8 tipos iniciais (iluminação, trânsito, vandalismo, espaço público, lixo, segurança, conflito social, outro) são populados por seed script via API.

### Encaminhamento como Agregação

A entidade Forwarding representa a ação formal do poder público de receber e tratar um conjunto de demandas similares. Ao invés de responder relato por relato, o agente agrupa relatos temática ou geograficamente próximos e encaminha o conjunto para o órgão competente. Essa agregação é a principal contribuição do sistema à eficiência da gestão pública.

### IA como Assistência (não Automação)

A IA (ChromaDB + sentence-transformers + OllamaClient) assiste o agente na fase de exploração, nunca tomando decisões. O sistema fornece: (1) busca semântica para encontrar relatos por conteúdo, (2) relatos similares a um relato selecionado, (3) chat NL para explorar padrões. O agente decide quais relatos agrupar e qual encaminhamento criar.

---

## 4. Permission Model

### System-Level Roles

| Role | Level | Capabilities |
|------|-------|-------------|
<!-- REQ-PERM-001 -->
| citizen | 1 | Registrar relatos (POST /reports); ver mapa público (GET /reports/geojson); ver detalhe de relato autenticado; usar busca semântica |
| agent | 2 | Tudo do citizen + criar/editar encaminhamentos (POST/PATCH /forwardings); ver painel de encaminhamentos; usar chat NL |
| admin | 3 | Tudo do agent + CRUD de ReportType (POST/PATCH/DELETE /report_types); gestão de usuários (future work) |

### Resource-Level Access

| Recurso | Regra de Acesso |
|---------|----------------|
| GET /reports/geojson | Público (sem auth) — mapa de relatos é dado público |
| GET /report_types | Público (sem auth) — cidadão precisa ver tipos no formulário |
| POST /reports | Requer role citizen, agent ou admin |
| POST /forwardings | Requer role agent ou admin |
| POST /report_types | Requer role admin |
| DELETE /report_types/{id} | Requer role admin |

> **Rationale:** O mapa de relatos e os tipos de problema são públicos para encorajar transparência e participação cidadã. Ações de escrita são protegidas por role para prevenir spam e garantir rastreabilidade.

---

## 5. Content Authoring & Attribution

- Todo relato (Report) é atribuído ao cidadão autenticado que o criou (author_id).
- Todo encaminhamento (Forwarding) é atribuído ao agente que o criou (agent_id).
- Não há conteúdo anônimo — toda escrita requer autenticação.
- Cidadãos não podem editar relatos de outros cidadãos.
- Agentes não podem editar relatos — apenas criar encaminhamentos.

---

## 6. Content Import & Export

### Export Formats

| Format | Output | Use Case |
|--------|--------|----------|
| GeoJSON | GET /reports/geojson | Visualização em mapa (Leaflet); integração com sistemas GIS |

### Import Formats

N/A — importação de dados externos é future work.

---

## 7. User Community & Localization

### Target Community

Moradores da Gávea (Rio de Janeiro) e servidores públicos da Prefeitura do Rio. Usuários de língua portuguesa, com familiaridade variável com tecnologia (do smartphone básico ao desktop profissional). Domínio: segurança e infraestrutura urbana.

### Localization Design

| Aspect | Primary | Secondary |
|--------|---------|-----------|
<!-- REQ-I18N-001 -->
| UI default language | pt-BR | — |
| Backend error default | pt-BR | — |

> O sistema é intencionalmente monolíngue pt-BR para o PoC. Internacionalização é future work.

---

## 8. User Experience Patterns (Domain-Driven)

<!-- REQ-UX-001 -->

### Mapa como Interface Principal

O mapa Leaflet centrado na Gávea é o ponto de entrada para cidadãos e agentes. Relatos são visualizados como marcadores coloridos por urgência (vermelho=alta, laranja=média, azul=baixa). Essa escolha reforça a dimensão geoespacial do problema: segurança urbana tem localização. A partir de D-008, o mapa é uma das visões intercambiáveis do workspace (ver abaixo), não mais a interface única.

### Workspace em Grid com Filtro Lateral e Visões Intercambiáveis

A rota `/` é um **workspace**: um painel lateral esquerdo fixo concentra o **estado do filtro** dos relatos (tipo, urgência, status, intervalo de data e um campo de **busca por texto semântico**), e o centro da aplicação exibe o **resultado desse filtro** em uma ou mais **visões intercambiáveis** sobre o mesmo conjunto: mapa georreferenciado (que também pode aplicar um filtro de `bbox` ao desenhar uma área), lista descritiva dos relatos, gráficos agregados, tópicos/clusters semânticos inferidos (BERTopic), busca por relatos semanticamente similares (operando **fora** do filtro central, a partir de um relato-semente), e um chat RAG com os relatos no contexto. Todas as visões compartilham um único filtro central (linked views / cross-filtering): interagir com uma refiltra as demais, com cada mudança anunciada por `aria-live`. O mapa deixa de ser *a* interface e passa a ser *uma* visão. A **visibilidade inicial** das visões é definida pelo papel — cidadão: Mapa + Lista; agente/admin: as visões analíticas e de IA também — preservando um painel único para ambas as audiências (ver D-008).

### Formulário de Relato Geolocalizado

O botão "Usar minha localização" preenche automaticamente lat/lon via `navigator.geolocation.getCurrentPosition()`. Campos lat/lon permanecem editáveis para correção manual. Isso reduz fricção no registro e aumenta a precisão dos dados.

### Seleção Múltipla para Encaminhamento

No mapa, agentes autenticados veem checkboxes nos marcadores. Ao selecionar ≥1 relato, aparece um botão flutuante "Criar encaminhamento". Esse padrão torna o fluxo de agregação natural e visível: o agente literalmente "seleciona" os problemas que vai encaminhar.

### Chat NL como Assistente de Exploração

A caixa de chat flutuante no mapa permite que o agente faça perguntas em linguagem natural ("Quais postes estão apagados na rua Marquês de São Vicente?"). A IA recupera relatos relevantes via RAG e os cita na resposta. O agente pode clicar nos relatos citados para ver detalhes no mapa.

---

## 9. Administrative Domain

### Activity Logging

Não implementado no PoC. Future work: log de auditoria para criação/edição de encaminhamentos.

### Backup & Restore

Banco SQLite em arquivo local (`fala_gavea.db`, gitignored). Backup via cópia do arquivo. Sem requisitos de recuperação formal no PoC.

### Terms & Conditions

Dados de cidadãos ficam exclusivamente na máquina local (conforme princípio C1 da constituição). Sem termos de uso formais no PoC.

---

## 10. Validation Constants (Domain)

| Constant | Value | Domain Rationale |
|----------|-------|-----------------|
<!-- REQ-VAL-001 -->
| Report.text | 10–2000 chars | Mínimo garante descrição útil; máximo previne spam |
| Report.lat | -90.0 a 90.0 | Latitude válida |
| Report.lon | -180.0 a 180.0 | Longitude válida |
| ReportType.name | 3–100 chars | Nomes de tipo devem ser descritivos mas concisos |
| Forwarding.institution | 3–200 chars | Nome do órgão pode ser longo |
| Forwarding.proposed_solution | 20–5000 chars | Solução deve ser descritiva |
| User.name | 2–100 chars | — |
| User.email | RFC 5321 | — |
| JWT access token expiry | 24h | Sessão de trabalho típica de um agente/cidadão |

---

# Part II — Metacommunication

## 11. Global Metacommunication Vision

Eu sei que você — seja cidadão, agente público ou administrador — vive e trabalha na Gávea e se preocupa com a qualidade do espaço urbano. Aprendi que problemas como postes apagados, buracos e situações de risco raramente chegam ao poder público de forma organizada: ficam no boca-a-boca, nos grupos de WhatsApp, ou simplesmente não chegam.

Projetei o fala-gavea para você de três formas: se você é cidadão, criei um formulário simples onde você registra o problema onde está, com a sua localização e uma foto opcional. Se você é agente público, criei um mapa que agrega todas as demandas registradas, com ferramentas de busca e agrupamento para que você possa criar encaminhamentos formais para os órgãos certos, com muito menos esforço manual. Se você é administrador, criei controles para configurar o sistema conforme a realidade da sua gestão.

A IA está presente para ajudar você a explorar os dados — não para tomar decisões no seu lugar. Você pode perguntar em linguagem natural, encontrar relatos similares e entender padrões. A decisão de encaminhar, para qual órgão e com qual solução proposta, é sempre sua.

---

## 12. Extended Metacommunication Template Guiding Questions

1. Analysis
   1.1. O que eu sei sobre você e como:
   Tenho três personas centrais derivadas dos casos de uso do roadmap-000071: (1) Cidadão morador da Gávea que usa smartphone e quer registrar um problema urbano sem burocracia; (2) Agente público que precisa organizar demandas e criar encaminhamentos formais; (3) Administrador que configura os tipos de problema. Ver `product-design/project/ux-research-results.md §1` para perfis completos.
   1.2. O que eu sei sobre afetados indiretos:
   Órgãos públicos receptores dos encaminhamentos (RioLuz, COMLURB, etc.) não são usuários do sistema, mas são destinatários dos encaminhamentos. A população da Gávea como um todo se beneficia indiretamente da resolução das demandas.
   1.3. Contextos de uso previstos:
   Cidadão: uso mobile, in loco, ao ver o problema. Agente: uso desktop, durante turno de trabalho, revisando demandas acumuladas. Administrador: uso ocasional para configurar tipos.
   1.4. Questões éticas:
   Dados de localização de cidadãos são sensíveis. Princípio C1 (dados nunca saem da máquina local) mitiga o risco no PoC.

2. Design
   2.1. O que projetei para você:
   Mapa interativo com relatos geolocalizados, formulário de registro simplificado, painel de encaminhamentos, busca semântica, chat NL assistido por IA.
   2.2. Quais objetivos estou apoiando:
   Cidadão: registrar problema sem burocracia. Agente: explorar demandas eficientemente e criar encaminhamentos formais. Administrador: manter a taxonomia de problemas atualizada.
   2.3. Em que situações aceito que você use:
   Cidadão usa in loco ao observar problema urbano. Agente usa durante plantão de triagem de demandas. Admin usa ao identificar novo tipo de problema recorrente.
   2.4. Como você deve usar:
   Ver journeys em §15 abaixo.
   2.5. Para que não quero que use:
   Denúncias anônimas de pessoas; spam de relatos falsos; uso da IA como decisor automatizado (a decisão de encaminhar é sempre do agente).
   2.6. Princípios éticos:
   Privacidade de dados cidadãos (local-only); transparência (mapa público); controle humano sobre decisões de encaminhamento.
   2.7. Alinhamento ético:
   Dados permanecem locais (C1). Mapa é público. IA é assistência, não automação (D-E).

---

## 13. Solution Representations

### Option B: User Stories

#### US-001: Cidadão registra relato de poste apagado

- **Story:** Como cidadão, quero registrar um problema de segurança urbana (ex: poste apagado) para que o poder público tome ciência e providências.
- **Goals:** G-001: Registrar problema sem burocracia. G-002: Confirmar que o registro foi recebido.
- **Problem Scenario:** R-PS-001 (cidadão vê poste apagado à noite, não sabe como avisar a prefeitura).
- **Acceptance Criteria:**
  - Cidadão acessa site, faz login, preenche formulário com tipo, urgência, texto e localização GPS.
  - Formulário preenche lat/lon automaticamente via geolocalização.
  - Relato aparece no mapa público após envio.
  - Status inicial é `pendente`.

#### US-002: Agente público cria encaminhamento para RioLuz

- **Story:** Como agente público, quero selecionar relatos de postes apagados na Gávea e criar um encaminhamento formal para a RioLuz.
- **Goals:** G-001: Organizar demandas similares. G-002: Criar encaminhamento rastreável.
- **Acceptance Criteria:**
  - Agente acessa mapa, filtra por tipo "Iluminação pública".
  - Agente seleciona múltiplos marcadores via checkbox.
  - Modal de encaminhamento permite inserir institution e proposed_solution.
  - Ao confirmar, relatos ficam com status `encaminhado`.
  - Encaminhamento aparece no painel do agente com status `aguardando_solucao`.

#### US-003: Agente usa busca semântica para explorar relatos

- **Story:** Como agente público, quero buscar relatos por conteúdo em linguagem natural para identificar padrões antes de criar um encaminhamento.
- **Goals:** G-001: Encontrar relatos temáticamente relacionados. G-002: Reduzir tempo de triagem.
- **Acceptance Criteria:**
  - Campo de busca na sidebar do mapa aceita texto livre.
  - Resultados aparecem como pins roxos em layer separado.
  - Chat NL responde perguntas e cita IDs dos relatos usados como contexto.

---

## 14. Per-Feature Metacommunication Intentions

| Feature / Flow | Designer Intent | Priority | Source | Last Synced |
|---|---|---|---|---|
<!-- REQ-MC-001 -->
| Formulário de relato com geolocalização | Eu reduzo a fricção de registro para você, cidadão, porque você está no local do problema e não deve precisar digitar endereço | P0 | human | 2026-06-17 20:07 UTC |
| Mapa público de relatos | Eu torno os problemas visíveis para você e para toda a comunidade porque transparência é pré-requisito para pressão cívica | P0 | human | 2026-06-17 20:07 UTC |
| Seleção múltipla no mapa para encaminhamento | Eu torno o agrupamento de demandas natural para você, agente, porque encaminhar problema por problema é ineficiente | P0 | human | 2026-06-17 20:07 UTC |
| Busca semântica de relatos | Eu ajudo você a encontrar relatos similares mesmo quando descritos em palavras diferentes, porque cidadãos não usam vocabulário padronizado | P1 | human | 2026-06-17 20:07 UTC |
| Chat NL assistente | Eu respondo suas perguntas sobre as demandas em linguagem natural para você, agente, porque explorar um banco de dados por filtros é lento para padrões emergentes | P1 | human | 2026-06-17 20:07 UTC | <!-- STATUS: implemented | plan-000100 | 2026-06-19 --> |

---

## 15. Designed User Journeys

### JM-TB-001: Cidadão registra relato de problema urbano

- **Persona:** R-P-001 (Cidadão)
- **Solution Scenario:** US-001
- **Goal:** Registrar problema urbano com localização e descrição
- **Pre-conditions:** Cidadão está autenticado; ReportTypes estão populados pelo admin.

#### Steps

| # | Action | Touchpoint | User Emotion | Pain Point | Opportunity |
| - | ------ | ---------- | ------------ | ---------- | ----------- |
| 1 | Acessa report.html (formulário de relato) | Browser mobile | Motivado | Pode não saber a URL diretamente | Link direto do mapa (botão flutuante para cidadão autenticado) |
| 2 | Seleciona tipo de problema no dropdown | Formulário web | Neutro | Tipo adequado pode não estar na lista | Admin mantém lista atualizada; opção "Outro" sempre presente |
| 3 | Seleciona urgência | Formulário web | Neutro | — | Dicas visuais (cor) para urgência |
| 4 | Digita descrição do problema | Formulário web | Engajado | Não sabe quanto detalhar | Placeholder com exemplo de descrição útil |
| 5 | Clica "Usar minha localização" | Botão geolocalização | Satisfeito | Permissão de geolocalização pode ser negada | Fallback: campos lat/lon editáveis |
| 6 | Opcionalmente adiciona photo_url | Campo de texto | Neutro | Upload de imagem não está disponível | Instrução clara: "Cole a URL de uma foto" |
| 7 | Clica "Registrar" | Botão submit | Aliviado | — | Confirmação visual (toast) + redirect para mapa mostrando o novo relato |

#### Post-conditions / Outcomes

O relato aparece no mapa público com status `pendente`. O cidadão pode ver seu relato registrado no mapa.

---

### JM-TB-002: Agente público cria encaminhamento

- **Persona:** R-P-002 (Agente público)
- **Solution Scenario:** US-002
- **Goal:** Agrupar relatos similares e encaminhar para órgão responsável
- **Pre-conditions:** Agente autenticado com role=agent; existem relatos com status `pendente` ou `em_analise`.

#### Steps

| # | Action | Touchpoint | User Emotion | Pain Point | Opportunity |
| - | ------ | ---------- | ------------ | ---------- | ----------- |
| 1 | Acessa index.html (mapa) com login de agente | Browser desktop | Focado | — | Layout responsivo para tablet também |
| 2 | Filtra por tipo/urgência/status na sidebar | Controles de filtro | Analítico | Muitos relatos simultâneos | Resumo de contagem por filtro |
| 3 | Opcionalmente usa busca semântica ou chat | Campo de busca / chat | Curioso | Resultados de IA podem ser imprecisos | Clareza de que IA é assistência; agente confirma seleção manualmente |
| 4 | Seleciona relatos via checkbox nos marcadores | Mapa Leaflet | Deliberativo | Difícil selecionar marcadores próximos | Clustering de marcadores próximos; tooltip com resumo |
| 5 | Clica botão flutuante "Criar encaminhamento" | Botão flutuante | Decisivo | — | Contador de relatos selecionados no botão |
| 6 | Preenche institution e proposed_solution no modal | Modal | Concentrado | — | Autocomplete de institutions já usadas |
| 7 | Confirma encaminhamento | Botão confirmar | Satisfeito | — | Toast de confirmação + link para painel do agente |

#### Post-conditions / Outcomes

Forwarding criado com status `aguardando_solucao`. Todos os Reports incluídos transitam para `encaminhado`. O encaminhamento aparece no painel agent.html.

---

### JM-TB-003: Explorar, filtrar e analisar relatos no workspace

- **Persona:** R-P-001 (Cidadão) e R-P-002 (Agente público)
- **Solution Scenario:** US-003
- **Goal:** Filtrar o conjunto de relatos e lê-lo por múltiplas visões (mapa, lista, gráficos, tópicos, similares, chat RAG)
- **Pre-conditions:** Usuário autenticado; relatos indexados nos espaços semânticos (roadmap-00002); endpoints `GET /reports/geojson`, `GET /reports/topics` e `POST /chat` disponíveis.

#### Steps

| # | Action | Touchpoint | User Emotion | Pain Point | Opportunity |
| - | ------ | ---------- | ------------ | ---------- | ----------- |
| 1 | Acessa `/` e vê o workspace: filtro à esquerda, visões ao centro | Workspace | Orientado | "Não é pra mim" se parecer dashboard de analista | Defaults por papel: cidadão vê Mapa+Lista; agente vê as visões analíticas |
| 2 | Aplica filtros (tipo/urgência/status/data) e busca por texto semântico no painel esquerdo | FilterPanel lateral | Analítico | — | Contagem viva ("142 relatos") em `aria-live` |
| 3 | Liga/desliga visões no centro | Toggle de visões | No controle | Não saber o que cada visão faz | Rótulo + 1 linha de auto-explicação por visão |
| 4 | Desenha uma área no mapa para filtrar por `bbox` | Mapa Leaflet | Curioso | Arraste é gesto hostil a teclado/a11y | Caminho alternativo por botão/teclado; alvos ≥44px |
| 5 | Lê padrões nos gráficos e nos tópicos inferidos do subconjunto filtrado | Gráficos + Tópicos | Perspicaz | IA pode ser imprecisa | Deixar claro que IA é assistência, não verdade |
| 6 | Seleciona um relato e busca similares **ignorando o filtro atual** | Painel de Similares | Investigativo | Confundir "similares" com "filtrados" | Rótulo explícito: "Similares em toda a base, fora do filtro" |
| 7 | (Agente) pergunta em linguagem natural ao chat RAG sobre os relatos | Chat RAG | Deliberativo | Saber quais relatos a IA usou | Respostas citam `cited_report_ids` clicáveis |
| 8 | (Agente) seleciona relatos no mapa ou na lista e cria encaminhamento | Map/Lista → CreateForwardingDialog | Decisivo | Seleção presa só ao mapa hoje | `selectedIds` no store compartilhado → SelectionBar única |

#### Post-conditions / Outcomes

O usuário compreende padrões no subconjunto filtrado por múltiplas visões. O agente pode partir da exploração para um encaminhamento (transição para JM-TB-002). O chat RAG (passo 7) e o encaminhamento (passo 8) são restritos a agente/admin; cidadão acessa as visões de transparência (Mapa, Lista, Gráficos).

---

## 16. Conceptual Design Delta

### New (in as-intended but not in as-coded)

| Section | Element | Description |
|---|---|---|
<!-- REQ-DELTA-001 -->
| §2 Entities | User, ReportType, Report, Forwarding, ForwardingReport | Todas as entidades definidas no design intent, nenhuma implementada ainda |
| §4 Permission Model | citizen/agent/admin roles | Modelo de roles definido, não implementado |
| §8 UX Patterns | Mapa, geolocalização, seleção múltipla, chat NL | Padrões UX definidos, frontend não implementado |
| §8 UX Patterns | Workspace em grid (filtro lateral + visões intercambiáveis) | Padrão definido (research-000092, D-008), frontend não implementado |
| §15 Journeys | JM-TB-001, JM-TB-002 | Journeys definidas, sistema não implementado |
| §15 Journeys | JM-TB-003 | Jornada de exploração/análise em workspace definida (research-000092); backends `/reports/topics` e `/chat` prontos, frontend não implementado |

### Changed (differs between as-coded and as-intended)

_N/A — projeto greenfield, nenhum código implementado ainda._

### Removed (in as-coded but not in as-intended)

_N/A._

---

## 17. Metacommunication Delta

### New Intentions (not yet implemented)

| Feature / Flow | Designer Intent | Priority |
|---|---|---|
| Formulário de relato com geolocalização | REQ-MC-001 | P0 |
| Mapa público de relatos | REQ-MC-001 | P0 |
| Seleção múltipla para encaminhamento | REQ-MC-001 | P0 |
| Busca semântica de relatos | REQ-MC-001 | P1 |
| Chat NL assistente | REQ-MC-001 | P1 | <!-- STATUS: implemented | plan-000100 | 2026-06-19 --> |

### Changed Intentions / Deprecated Intentions

_N/A — projeto greenfield._

---

## Decisions

<!-- STATUS: proposed -->
### D-001: Novo projeto independente via python-scaffold

**Context**: O sistema fala-gavea poderia ser adicionado como módulo ao projeto kb-qa existente em INF2921/inf2921-grupo-c, ou criado como projeto independente. O roadmap-000071 superseeded um roadmap anterior (000070) de escopo mais amplo.

**Decision**: Novo projeto independente no diretório `fala-gavea/` gerado por `/python-scaffold`. Stack: FastAPI + SQLAlchemy + SQLite + Pydantic v2 + pytest.

**Consequences**: Isolamento limpo entre o sistema de demandas e o kb-qa existente. Permite desenvolver sem interferir no outro projeto. Requer configuração completa do zero (harness SEJA, CLAUDE.md, etc.).

---

<!-- STATUS: proposed -->
### D-002: Tipos de problema dinâmicos via tabela ReportType

**Context**: Os tipos de problema urbano (iluminação, trânsito, etc.) poderiam ser hardcoded como Enum Python, ou gerenciados dinamicamente em banco de dados.

**Decision**: Tabela `ReportType` gerenciada pelo admin via API. Os tipos não são Enum hardcoded. Admin faz CRUD via endpoints protegidos. 8 tipos iniciais populados por seed script via API.

**Consequences**: Admin pode adicionar "drenos entupidos" sem redeploy. Adiciona complexidade de CRUD para admin, mas reflete a realidade de gestões municipais onde categorias evoluem. O seed script garante que o bootstrap exercita a API.

---

<!-- STATUS: proposed -->
### D-003: Autenticação simples JWT Bearer para PoC

**Context**: O sistema requer autenticação para diferenciar cidadão, agente e admin. Opções: fastapi-users (biblioteca pesada), OAuth externo (Google/GitHub), JWT simples com PyJWT.

**Decision**: JWT Bearer via PyJWT + passlib[bcrypt]. Roles: citizen, agent, admin. Registro aberto via POST /auth/register + POST /auth/token. Sem OAuth externo. Token expiry: 24h. Foto: photo_url é campo de texto (URL), sem upload.

**Consequences**: Simples de implementar e entender no contexto de PoC. Não escala para produção sem refresh tokens e rate limiting. Upload de imagem fica como future work (photo_url como campo livre é aceitável para PoC).

---

<!-- STATUS: proposed -->
### D-004: Forwarding como agregação many-to-many de relatos

**Context**: Um encaminhamento poderia referenciar apenas um relato (1:1) ou múltiplos (many-to-many). O caso de uso principal é o agente agrupando relatos similares.

**Decision**: `Forwarding` agrupa N relatos via tabela `ForwardingReport` (FK dupla). Um relato pode estar em múltiplos encaminhamentos (problema recorrente). Status: `aguardando_solucao | solucao_em_andamento | finalizado`.

**Consequences**: Modelo more expressivo que representa a realidade de gestão pública. Requer join table. A query para listar encaminhamentos com seus relatos é mais complexa.

---

<!-- STATUS: proposed -->
### D-005: IA como assistência, não automação

**Context**: A IA poderia auto-categorizar relatos, sugerir automaticamente encaminhamentos, ou apenas assistir o humano na exploração.

**Decision**: ChromaDB + sentence-transformers para busca semântica e relatos similares. Chat NL como assistente de busca (OllamaClient com modelo local qwen3:8b). Sem auto-categorização ou sugestão automática de encaminhamento no roadmap atual.

**Consequences**: Controle humano preservado. Decisões de encaminhamento são auditáveis e responsáveis. IA local (Ollama) garante que dados cidadãos nunca saem da máquina (princípio C1). Limitação: qualidade da busca depende do modelo de embeddings e do modelo Ollama disponível localmente.

---

<!-- STATUS: proposed -->
### D-006: Frontend HTML estático + Leaflet sem framework JS

**Context**: O frontend poderia ser React/Vue, ou HTML estático com bibliotecas mínimas.

**Decision**: HTML estático + Leaflet (mapa) + Alpine.js (interatividade de estado). Servido pelo FastAPI StaticFiles. Páginas: index.html (mapa), agent.html (painel de encaminhamentos), login.html, report.html.

**Consequences**: Zero build step. Simplicidade adequada ao PoC. Sem SPA — navegação entre páginas recarrega. Alpine.js é suficiente para checkboxes, modais e filtros. Limitação: sem hot reload no desenvolvimento (mas pode ser servido diretamente pelo uvicorn --reload).

---

### D-007: Frontend SPA React+Vite+TS+Tailwind supersedes D-006

**Context**: O plano wave-1-item-4 recebeu feedback do usuário para usar tecnologias frontend mais modernas ("fugir das páginas estáticas e ficar com um visual mais fluido e moderno"). A decisão D-006 havia especificado HTML estático + Alpine.js + Leaflet.

**Decision**: SPA React 18 + Vite + TypeScript com Tailwind CSS + shadcn-style (Radix primitives) + react-leaflet. Build para `static/` servido pelo FastAPI StaticFiles (mesmo modelo de servir da D-006, mantido). CORS intencionalmente ausente: dev usa proxy Vite, prod é same-origin. Toolchain npm adicionado (`frontend/`).

**Consequences**: Passo de build introduzido (`npm run build`). Interação mais fluida (SPA, sem reload entre páginas). Vitest + RTL para testes frontend. D-006 supersedida.

---

### D-008: ### D-008: Workspace em grid de ferramentas substitui o modelo map-centric


**Context**: O SPA era map-centric (rota `/` = MapPage em tela cheia; o mapa E a visualizacao; busca semantica e chat como placeholders sobre o mapa). O time quer inverter para um modelo de workspace/dashboard que sirva tanto a transparencia civica (cidadao) quanto a analise territorial (agente), apoiando os dois projetos educacionais (Canal Digital / Waze comunitario; Mapa Colaborativo de Dados).

**Decision**: O painel central de `/` vira um grid de widgets onde o mapa e apenas um deles. Iteracao 1: Mapa, Tabela/lista, Graficos agregados, Topicos/clusters semanticos. Painel unico para ambas as audiencias, com visibilidade inicial dos widgets definida pelo papel (cidadao: Mapa+Tabela; agente: os 4). Layout base fixo com toggle de ferramentas. Linked views: um store de filtro/selecao compartilhado (Zustand) com cross-filtering; react-query continua so com dados de servidor.

**Consequences**: Filtro/selecao sobem do MapPage local para um store compartilhado. Nova jornada JM-TB-003 (explorar/analisar relatos). SelectionBar->CreateForwardingDialog passa a funcionar do Mapa e da Tabela. Introduz Recharts (charting) e clustering de marcadores. Widget de Topicos depende das Waves 1/2 (sequenciado por ultimo, atras de placeholder digno). a11y de cross-filter (teclado, alvos >=44px, nao-so-cor, aria-live) torna-se requisito.

*Source: from research-000092 (2026-06-19)*

### D-009: Filtro encenado (draft + Aplicar) substitui o cross-filtering ao vivo do D-008


**Context**: O FilterPanel do workspace (D-008) aplicava filtros ao vivo -- cada mudanca de filtro (incluindo a busca semantica, sem debounce) re-disparava fetch geojson e busca semantica imediatamente. Feedback do usuario: o painel lateral esquerdo e o coracao da busca e precisa comunicar claramente os filtros ativos e dar controle explicito sobre quando aplicar.

**Decision**: Introduzir um modelo encenado (staged). O FilterPanel edita um draftFilters (slice separado no Zustand); um botao Aplicar comita draft -> filters e so entao as visoes re-buscam. Indicador de filtros alterados (dirty) + chips de filtros ativos com remocao individual; Limpar mantido. Manipulacao direta (bbox desenhado no mapa, Similares na tabela) comita imediatamente; apenas campos do painel sao encenados. aria-live para dirty/chips.

**Consequences**: O store ganha um slice draftFilters paralelo a filters; consumidores leem so o comitado. Busca semantica deixa de disparar por tecla (resolvido pelo Apply, dispensando debounce). Diverge da intencao filtro ao vivo, lente unica do D-008.

**Rejected Alternatives**: (a) Manter filtro ao vivo e apenas adicionar debounce (~350ms) na busca semantica + chips de filtro ativo -- mais leve e preserva a intencao do D-008, mas nao oferece o gesto explicito de Aplicar que o usuario pediu. (b) Status quo (tudo ao vivo, sem debounce) -- mantem carga por tecla na busca semantica.

*Source: from research-000129 (2026-06-21)*

## CHANGELOG

2026-06-17 | D-001 | added | - | Decisao de novo projeto independente via python-scaffold (roadmap-000071 D-A)
2026-06-17 | D-002 | added | - | Tipos de problema dinamicos via ReportType (roadmap-000071 D-B)
2026-06-17 | D-003 | added | - | Auth JWT Bearer simples para PoC (roadmap-000071 D-C)
2026-06-17 | D-004 | added | - | Forwarding como agregacao many-to-many (roadmap-000071 D-D)
2026-06-17 | D-005 | added | - | IA como assistencia, nao automacao (roadmap-000071 D-E)
2026-06-17 | D-006 | added | - | Frontend HTML estatico + Leaflet (roadmap-000071 D-F)
2026-06-18 | D-007 | added | - | Frontend SPA React+Vite+TS+Tailwind supersede D-006 (plan-000082)
2026-06-19 | JM-TB-003 | added | §15 | Jornada de exploração/análise em workspace; §8 ganha padrão de filtro lateral + visões intercambiáveis (research-000092, D-008)
