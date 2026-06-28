# Communication 000187 | ACD | 2026-06-28 13:13 UTC | Academics

> Source: este material reformata e expande o roteiro de apresentacao consolidado em `_output/research-logs/research-000186-discurso-professores-fala-gavea.md`, com a fronteira "entregue vs. idealizado" auditada em `_output/research-logs/research-000185-fase5-text-vs-implementation-gap.md`. Toda afirmacao sobre o que existe esta ancorada em `product-design/project/product-design-as-coded.md` e no codigo em `src/fala_gavea/`.

---

## Visao geral do projeto

**fala-gavea** e um sistema de demandas de cidadaos para seguranca urbana no bairro da Gavea (Rio de Janeiro), construido para a disciplina INF2921/CIS2114 - AI Systems Design (2026.1, PUC-Rio). Equipe: Andrey, Mauro, Julia, Herbert, Natali.

**Proposta de valor.** O sistema fecha um laco hoje quebrado: o cidadao registra um problema georreferenciado (localizacao, tipo, urgencia); o agente publico tria e cria um encaminhamento institucional que agrega varios relatos num unico orgao competente, com status e solucao proposta; e uma camada de IA assiste a exploracao da base por busca semantica e chat em linguagem natural.

**Diferencial e tese de projeto.** A IA e tratada como *auxiliar auditavel da curadoria, nunca como curador principal*. Cada resposta gerada cita sua fonte, nenhuma sugestao da IA e auto-aplicada, e a arquitetura mantem toda a IA atras de portas plugaveis. O humano permanece no comando da decisao. Esta comunicacao narra o que de fato foi entregue, em seis secoes, e separa explicitamente o entregue do idealizado/trabalho futuro - uma distincao que tratamos como exigencia de rigor academico, nao como ressalva.

**Nota terminologica (audiencia interdisciplinar).** Usamos *relato* para a demanda registrada pelo cidadao; *encaminhamento* para o ato institucional de agregar relatos e direciona-los a um orgao; *RAG* (Retrieval-Augmented Generation) para a geracao de texto condicionada a documentos recuperados; *embedding* para a representacao vetorial densa de um texto. A IA e *auditavel* no sentido de que toda saida gerada e rastreavel ate as fontes que a produziram.

---

## 1. O Problema

A seguranca urbana na Gavea depende de um fluxo que hoje esta quebrado nas duas pontas, conforme os cenarios levantados na pesquisa de UX (R-PS-001, R-PS-002).

**Do lado do cidadao (persona R-P-001).** O morador ve um problema - poste apagado, buraco, lixo acumulado - e nao tem um canal claro. Tenta o 1746 e fica em espera; pesquisa no Google e cai no orgao errado; manda no WhatsApp da associacao e ninguem responde. Desiste, e o problema persiste por semanas. A frustracao central, registrada na pesquisa, e: *"reportei e nunca soube o que aconteceu"* - ou seja, ausencia de canal **e** de transparencia.

**Do lado do agente publico (persona R-P-002).** O agente recebe demandas de multiplos canais (telefone, e-mail, WhatsApp, 1746) e tria uma lista de texto plana, sem mapa e sem agrupamento. Tres relatos do mesmo poste - "luz apagada", "poste sem luz", "rua escura" - viram tres encaminhamentos distintos para a RioLuz, que despacha tres equipes ao mesmo local. A triagem manual consome tempo e duplica trabalho, porque o agente nao dispoe de visao geoespacial nem de meios para reconhecer demandas semanticamente equivalentes.

**O laco a fechar.** O problema e, portanto, duplo: o cidadao nao tem onde registrar com transparencia, e o agente nao tem como explorar e agrupar demandas similares de forma eficiente. fala-gavea fecha o laco cidadao -> agente -> cidadao numa unica solucao.

---

## 2. Casos de Uso

Tres casos de uso ancoram o sistema (User Stories, secao 13 do design as-intended):

- **US-001 - Cidadao registra um relato georreferenciado.** *"Como cidadao, quero registrar um problema (ex.: poste apagado) para que o poder publico tome ciencia."* Criterios: login -> formulario (tipo, urgencia, texto livre, GPS automatico) -> o relato aparece no mapa publico com status `pendente`.
- **US-002 - Agente cria encaminhamento institucional.** *"Como agente, quero selecionar relatos de postes apagados e encaminhar formalmente a RioLuz."* Criterios: filtra por tipo -> seleciona multiplos relatos -> informa instituicao + solucao proposta -> os relatos passam a `encaminhado`; o encaminhamento nasce no estado `aguardando_solucao`.
- **US-003 - Agente explora por busca semantica.** *"Como agente, quero buscar por conteudo em linguagem natural para achar padroes antes de encaminhar."* Criterios: busca textual livre -> resultados e relatos similares -> chat em linguagem natural que **cita os IDs dos relatos** usados como contexto.

---

## 3. Jornadas

Cada caso de uso virou uma jornada projetada, e as tres estao implementadas ponta a ponta (frontend React + backend FastAPI). A correspondencia jornada -> implementacao foi auditada em research-000185.

- **JM-TB-001 (Cidadao registra).** Acessa o formulario -> escolhe tipo/urgencia -> descreve -> "Usar minha localizacao" (geolocalizacao do navegador, com fallback de lat/lon editavel) -> opcionalmente um `photo_url` -> "Registrar" -> toast de confirmacao e redirecionamento para o mapa, ja com o novo marcador.
- **JM-TB-002 (Agente encaminha).** Abre o workspace -> filtra -> (opcional) usa busca semantica/chat -> seleciona relatos -> "Cesta de relatos" -> preenche instituicao + solucao proposta -> confirma -> os relatos passam a `encaminhado` e o encaminhamento aparece no painel do agente.
- **JM-TB-003 (Explorar/analisar).** O workspace e um grid com filtro a esquerda e **visoes intercambiaveis** ao centro: Mapa, Tabela, Palavras-chave, Similares, Chat e Cesta. Os defaults variam por papel: o cidadao ve Mapa + Tabela (transparencia); o agente/admin ve as visoes analiticas. A IA aparece como **mais uma lente**, sempre citando de onde tirou a resposta.

**Gesto de design.** O humano esta no comando. A IA assiste, nunca decide - principio que se materializa nas features a seguir (ver secao 4) e na arquitetura de portas (ver secao 5).

---

## 4. Features do Sistema

O que esta, de fato, no ar. Cada feature abaixo corresponde a endpoints concretos verificaveis em `src/fala_gavea/presentation/api/routers/`.

**Cidadao / transparencia**

- Registro de relato georreferenciado (tipo, urgencia, texto, lat/lon, `photo_url`) via `POST /reports`.
- **Relato anonimo:** coordenadas arredondadas (3 casas decimais, para reduzir reidentificacao) + token de reivindicacao unico; consulta posterior via `GET /reports/mine?anonymous_token=`.
- Mapa publico clusterizado (react-leaflet-cluster) e exportacao GeoJSON (RFC 7946) via `GET /reports/geojson`.
- **Transparencia do encaminhamento sem login:** `GET /forwardings/public`, acompanhamento de um encaminhamento, listagem dos encaminhamentos de um relato; alem de "Meus relatos" e "Meus encaminhamentos" para o usuario autenticado.
- **Feedback civico:** votos (up/down) e comentarios em relatos e encaminhamentos.

**Agente / curadoria**

- Workspace em grid: filtro encenado (rascunho + "Aplicar"), chips de filtro ativo, e presets de filtro salvos (entidade `SavedFilter`).
- **Encaminhamento como agregacao:** N relatos -> 1 instituicao, com solucao proposta e ciclo de status (`aguardando_solucao` -> `solucao_em_andamento` -> `finalizado`). A relacao N-para-1 e modelada pela entidade de juncao `ForwardingReport`.
- Endpoint unificado de consulta `POST /reports/query`: filtros multivalor + ranqueamento semantico + paginacao.

**Camada de IA (assistencia)**

- **Busca semantica** de relatos (`GET /reports/search`) e **relatos similares** (`GET /reports/{id}/similar` e, por conjunto, `POST /reports/similar-to-set`).
- **NL -> filtro** (`POST /nl/filter`): o agente descreve a intencao em linguagem natural e o sistema *propoe* um filtro - mas **nunca auto-aplica**; o usuario precisa clicar "Aplicar sugestao ao rascunho". As dimensoes traduziveis sao deliberadamente limitadas a tipo de relato, urgencia, status, janela temporal (`since`/`until`) e texto/busca; nao ha dimensao geografica/bairro no parser (uma restricao consciente, ver nota de escopo abaixo).
- **Chat RAG** (`POST /nl/chat`): pergunta em linguagem natural sobre os relatos; a resposta **cita os IDs** dos relatos usados como contexto (`cited_report_ids`), tornando cada afirmacao rastreavel.
- **Palavras-chave** por TF-IDF + K-means (`GET /reports/keywords`) sobre o subconjunto filtrado - extracao lexica barata, sem modelo de embedding.
- **Helper da plataforma** (`POST /nl/help`): um *segundo* chat RAG, sobre a propria documentacao do projeto (como a plataforma funciona), com filtro de visibilidade por papel (citizen/agent veem conteudo publico; admin recebe tambem conteudo interno e um enquadramento "meta").
- **Marcador de proveniencia de IA** (`AiBadge`) visivel em toda a interface onde a IA atua - uma escolha de comunicabilidade, que sinaliza ao usuario a fronteira entre conteudo humano e gerado.

**Admin**

- CRUD de tipos de problema (taxonomia dinamica, nao hardcoded; com soft-delete).
- Bootstrap de admin via variaveis de ambiente; importacao em lote de relatos/topicos via CSV; wipe do banco (SQLite + ChromaDB).

### Escopo honesto: o que NAO foi entregue (hipotese de design / trabalho futuro)

Para uma banca de AI Systems Design, a distincao mais importante e tambem a mais facil de obscurecer. As capacidades a seguir foram **pesquisadas e planejadas, mas nao implementadas**, e nao devem ser lidas como entregues:

- **Sugestao de categoria por IA.** Nao existe categorizacao automatica em lugar algum: o `report_type` e escolhido manualmente pelo cidadao no momento do registro. A superficie de IA entregue e exclusivamente busca semantica, similares, palavras-chave TF-IDF, chat RAG e NL -> filtro.
- **Edicao de categoria pelo agente.** Nao ha `PATCH /reports/{id}`; o relato e imutavel apos a criacao, exceto pelo `status` (auto-ajustado para `encaminhado` no momento do encaminhamento). Logo, nao ha correcoes de categoria acontecendo.
- **Evento de curadoria.** Nao existe entidade, tabela ou registro de "evento de curadoria". O inventario de entidades e: `user, report, report_type, forwarding, forwarding_report, comment, vote, saved_filter, anonymous_report_token`.
- **Loop de aprendizado por few-shot.** Nao ha corpus de correcoes nem mecanismo que realimente correcoes humanas em chamadas futuras do LLM. `BERTopic` esta instalado, porem **dormente** (nunca instanciado), reservado a uma exploracao futura.

Esse conjunto - sugestao de categoria -> correcao do agente -> evento de curadoria -> few-shot que realimenta a IA - constitui a **hipotese de design** central do projeto (pesquisada em research-000170/000172, planejada em plan-000174). Apresenta-la como entregue seria impreciso; apresenta-la como direcao futura testavel e a postura correta.

---

## 5. Arquitetura do Software

Arquitetura limpa em quatro camadas, com as dependencias apontando para dentro (regra da dependencia):

```
presentation/    FastAPI routers, dependencies.py (get_current_user, require_role), schemas Pydantic
        |
        v
application/      use cases - logica de negocio pura, sem DB nem HTTP
        |
        v
domain/           entidades (dataclasses puras) + interfaces de repositorio/portas (ABCs)
        ^
        |
infrastructure/   repos SQLAlchemy, ChromaDB, LLM (Ollama/Anthropic), embeddings
```

**Por que arquitetura limpa.** A decisao parte de um compromisso central: separar as regras de negocio das tecnologias que as servem. O core da aplicacao concentra-se nos casos de uso e nas entidades do dominio; toda funcionalidade externa (banco de dados, busca vetorial, LLM, embeddings) e acessada por meio de uma *porta* - uma interface de software declarada no dominio e implementada na infraestrutura. A injecao de dependencias ocorre em tempo de execucao (`dependencies.py`), o que torna o sistema configuravel: a mesma base de codigo se adapta a diferentes requisitos de hardware e as tecnologias disponiveis, bastando trocar a implementacao injetada atras de cada porta. Essa propriedade deixa de ser teorica na secao 6, quando as restricoes de producao nos obrigaram a reconfigurar a stack sem tocar no core.

Dois principios de fronteira merecem destaque, pois sao as decisoes que tornam o sistema testavel e seguro:

- **Toda IA e busca semantica passa por `infrastructure/`** (ChromaSearchClient, cliente Ollama/Anthropic). Nenhum use case ou router toca ChromaDB ou o LLM diretamente. As portas de dominio - `ISemanticSearchPort`, `IReportIndexer`, `ILLMClient`, `IDocSearchPort` - tornam a IA *plugavel* (trocar o provedor de LLM e mudanca de uma linha/uma variavel de ambiente) e *testavel* (use cases sao exercitados com dublês das portas, sem subir modelo). Esta e a operacionalizacao concreta do principio "IA como componente substituivel atras de contrato explicito".
- **Autenticacao centralizada.** Nenhum router le o JWT diretamente; tudo passa por `dependencies.py`. A atribuicao de autoria vem sempre do token (`author_id = current_user.id`), nunca do corpo da requisicao - o que previne falsificacao de autoria por construcao, e nao por validacao defensiva espalhada.

**Exemplo de fluxo (reproduzivel).** `POST /reports` -> use case `CreateReport` -> `report_repo.save()` -> hook opcional `indexer.index(report)`. Decisao de robustez: uma falha de indexacao semantica registra um WARNING e **nao** aborta o relato - a persistencia (fonte da verdade) e desacoplada da indexacao (derivada), de modo que a indisponibilidade da IA nunca impede o cidadao de registrar.

**Camada de apresentacao REST.** A apresentacao do backend e uma API REST, e nao um acoplamento a uma unica interface grafica. Isso permite que uma variedade de interfaces de usuario seja construida sobre o mesmo nucleo de casos de uso: o SPA React entregue e apenas um cliente possivel; outros (aplicativo movel, integracoes institucionais, ferramentas de linha de comando) consumiriam exatamente os mesmos endpoints. Essa abertura aproxima o projeto da nocao de *Developer as User* (referencia ao livro do Prof. Renato, da disciplina): o desenvolvedor que integra ou estende o sistema e, ele proprio, um usuario - e o contrato REST e a mensagem de metacomunicacao que o sistema enderaca a esse usuario, e nao apenas ao usuario final da interface grafica.

---

## 6. Stack Tecnologico Sustentando as Features

Cada peca da stack existe para sustentar uma feature concreta. A tabela mapeia tecnologia -> feature, de modo que um avaliador possa reconstruir a justificativa de cada escolha.

| Camada | Tecnologia | Feature que sustenta |
|---|---|---|
| **Persistencia (DB)** | SQLite + SQLAlchemy (ORM sincrono) | Relatos, encaminhamentos, votos, comentarios, filtros salvos, usuarios. **O SQL e a fonte da verdade dos filtros**; integridade referencial via PRAGMA de foreign keys. |
| **Busca vetorial (Chroma)** | ChromaDB + sentence-transformers (`intfloat/multilingual-e5-small`) | Busca semantica, similares e o **ranqueamento** do `POST /reports/query`. Padrao-chave: **o ChromaDB so ranqueia; o SQL filtra** (`rank(query, ids) -> scores`). Duas colecoes: relatos e self-docs (helper da plataforma). |
| **Clusterizacao lexica** | scikit-learn (TF-IDF + K-means) | Palavras-chave do subconjunto filtrado (`GET /reports/keywords`) - sem modelo de embedding, barato e interpretavel. |
| **LLM** | Ollama (local, `qwen3:8b` por padrao) **ou** Anthropic (configuravel por variavel de ambiente) | Chat RAG sobre relatos, NL -> filtro, helper da plataforma. **Privacidade:** com Ollama, o texto dos relatos permanece local; apenas com `provider=anthropic` trechos sao enviados a uma API externa. |
| **Auth** | JWT Bearer (PyJWT, HS256, expiracao de 24h) | Papeis citizen/agent/admin; acesso por recurso resistente a BOLA - recurso de terceiro retorna 404 em vez de 403, evitando vazamento de existencia. |
| **Frontend** | React 18 + Vite + TypeScript + Tailwind + react-leaflet (Zustand + react-query) | Workspace em grid, mapa, visoes intercambiaveis; buildado para `static/` e servido pelo proprio FastAPI (StaticFiles). |
| **Degradacao graciosa** | (transversal) | Sem Ollama/Chroma configurados, os endpoints de IA retornam **503** e o restante do sistema segue de pe - a IA e aditiva, nao um ponto unico de falha. |
| **Deploy** | Dockerfile multi-stage (node build -> python:3.13-slim), Railway, endpoint `/health` | Tudo configuravel por variavel de ambiente; `/data` e volume persistente. |
| **Testes** | pytest (backend) + vitest (frontend) | Verificacao automatizada das duas pontas da stack. |

### Empacotamento e restricoes de producao (Docker + Railway)

O sistema e empacotado num Dockerfile multi-stage (build do SPA React em node, runtime em `python:3.13-slim`) e implantado em producao na Railway. Essa etapa revelou uma licao de engenharia que vale registrar, porque expoe o valor pratico da arquitetura descrita na secao 5.

**Restricao de memoria em runtime.** O ambiente de producao disponivel impunha um teto de memoria que tornava inviavel executar um LLM local: rodar o Ollama exigiria hardware (RAM/CPU) que a Railway, na configuracao usada, nao oferecia. Diante disso, decidimos desabilitar em producao as features de IA mais custosas. A arquitetura tornou essa decisao barata: como a IA vive atras de portas com injecao de dependencias e degradacao graciosa, basta nao configurar o provedor para que os endpoints correspondentes retornem 503 - sem nenhuma alteracao no core de casos de uso e entidades. Foi exatamente a configurabilidade da secao 5 pagando dividendos sob restricao real: a separacao entre regra de negocio e tecnologia deixou de ser um argumento de design e virou a alavanca que permitiu adaptar o sistema ao hardware disponivel.

**Troca de BERTopic por TF-IDF.** Houve ainda uma decisao de qualidade e custo: a modelagem de topicos com BERTopic nao estava entregando topicos uteis, pois dependeria de um fine-tuning que nao executamos. Substituimos a extracao de topicos por palavras-chave via TF-IDF + K-means (scikit-learn), que e mais leve, dispensa modelo de embedding dedicado e produz clusters interpretaveis. O BERTopic permanece instalado, porem dormente, reservado a um trabalho futuro de fine-tuning. Alem do ganho de qualidade, a troca alivia a pressao de memoria, alinhando-se a restricao de producao acima.

### Fecho: a tese tecnica do projeto

A escolha de stack reflete a tese do projeto: **IA local, barata e auditavel** (Ollama, e5-small, TF-IDF) como assistente da curadoria humana. Tres propriedades resumem a contribuicao tecnica, e cada uma e verificavel no codigo:

1. **Rastreabilidade.** Cada resposta gerada cita sua fonte (`cited_report_ids` no chat RAG; `doc_type` nas citacoes do helper).
2. **Nao-imposicao.** Nada e auto-aplicado: o NL -> filtro propoe, o humano aceita.
3. **Substituibilidade.** A arquitetura limpa mantem a IA atras de portas plugaveis, com degradacao graciosa quando indisponivel.

O humano permanece no comando da curadoria. O que ficou de fora - sugestao de categoria por IA, evento de curadoria e o loop de few-shot (secao 4) - e a direcao de pesquisa natural a partir desta base entregue, e nao parte do que foi construido.
