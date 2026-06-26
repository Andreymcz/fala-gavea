# Research 000175 | fala-gavea | 2026-06-26 14:37 UTC | Chat helper RAG sobre a documentação do projeto

tags: rag, chat-assistant, security, architecture, chromadb, llm

## User brief

> chat helper para usuário. O chat acoplado ao sistema acessa um corpus de documentação ( que foi gerada neste mesmo projeto, podem ser os planos/researcher/comunications que foram gerados pelo seja + casos de uso e o que foi implementado. O chat é enriquecido com rag desses documentos e é um assistente para a comunicaçào do que é a plataforma

## Agent interpretation

O time quer uma **segunda** experiência de chat, distinta do chat de relatos já existente (`POST /nl/chat`). Este novo assistente — um "helper sobre a plataforma" — responde perguntas sobre **o que a Fala-Gávea é e como funciona**, ancorado por RAG sobre a *própria documentação do projeto*: os artefatos gerados pelo SEJA em `_output/` (planos, research-logs, reflections, communications) somados aos arquivos de `product-design/` (product-design-as-coded, jornadas, constituição, casos de uso). É um assistente de **metacomunicação/onboarding**, não de exploração de demandas.

Decisões já tomadas pelo usuário nesta sessão (via AskUserQuestion):
1. **Audiência**: todos os usuários autenticados (citizen, agent, admin).
2. **Corpus**: o corpus SEJA completo de `_output/` + `product-design/`.
3. **Relação com o chat atual**: feature separada — endpoint próprio (ex. `POST /nl/help`) + coleção ChromaDB própria.
4. **Provider LLM**: reaproveitar a factory atual (Ollama local por padrão, Anthropic opcional via `FALA_GAVEA_LLM_PROVIDER`).

## Files

Lidos / relevantes:
- `src/fala_gavea/application/use_cases/chat/answer_with_rag.py` — padrão a espelhar para `AnswerHelpWithRag`.
- `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py` — cliente de coleção única (`_COLLECTION_NAME` na linha 13); embeddings e5-small com prefixos `passage:`/`query:`.
- `src/fala_gavea/infrastructure/embeddings/registry.py` — `SemanticConfig` (um único `vectorstore_path`, linhas 13-19).
- `src/fala_gavea/presentation/api/routers/nl.py` — contrato 503 + rate-limit por usuário a reutilizar.
- `src/fala_gavea/presentation/api/dependencies.py` — padrão lazy-singleton (linhas 122-169) a espelhar em `get_doc_search_port()`.
- `src/fala_gavea/infrastructure/llm/factory.py` — seleção global de provider (relevante para C1/Anthropic).
- `product-design/project/constitution.md` — C1 (linha 45), S1/S3 (linhas 35-37).
- Corpus: `_output/plans` (88), `_output/research-logs` (19), `_output/reflections` (11), `_output/communication` (9), + `product-design/project/*`.

---

## Estado atual da arquitetura

- **Chat de relatos existente**: `AnswerWithRag` → `POST /nl/chat`, **somente agent+admin**. Recupera top-5 via `ISemanticSearchPort.search()` (retorna `(id, score)`), **hidrata o texto via SQL** (`IReportRepository`), monta system prompt pt-BR e chama `ILLMClient.complete()`. Retorna `RagAnswer(response, cited_report_ids)`.
- **ChromaSearchClient**: coleção única `falagavea_reports_search`, indexa `Report.text` curto (10–2000 chars), modelo `intfloat/multilingual-e5-small`. Singleton via `get_report_indexer()`; `get_semantic_search_port()` reusa o mesmo singleton (modelo carregado uma vez).
- **LLM**: `create_llm_client()` factory; `get_llm_client()` é lazy-singleton, retorna `None` se indisponível. Endpoints 503 quando LLM/busca indisponíveis.
- **Constituição relevante**: T1 (todo acesso LLM/semântico via `infrastructure/`), T2 (auth só via `dependencies.py`), C1 (dados de cidadão nunca saem da máquina — Ollama local), S1 (nenhum secret no código), S3 (busca/LLM são read-only no DB).

## Análise por perspectiva (síntese da revisão de especialista)

| Perspectiva | Veredito | Essência |
|---|---|---|
| **Segurança** | ⚠️ Bloqueador a mitigar | Corpus completo + audiência com cidadãos + superfície de chat = caminho de **divulgação de informação interna** (security-checklists, threat-model, alternativas rejeitadas, internals de planos). Nenhuma das 3 decisões isoladamente cria o risco; a combinação sim. |
| **Arquitetura** | ✅ Adotar (com prescrição) | Feature separada cabe bem na arquitetura limpa, mas **não** sobrecarregue `ISemanticSearchPort`. Novo `IDocSearchPort` que retorna o texto do chunk direto do Chroma (sem hidratação SQL). |
| **Dados/Privacidade (C1)** | ✅ Baixo risco | Docs do projeto ≠ dados de cidadão; C1 não é violado mesmo com Anthropic. Ressalva: garantir que o corpus não contenha PII real nem secrets (S1). |
| **API** | ✅ Adotar | `POST /nl/help` espelhando `/nl/chat` é consistente; retornar `cited_doc_paths`; manter contrato 503; **não** ecoar caminhos internos em erros para cidadãos. |
| **Performance** | ✅ Adequado p/ PoC | Corpus minúsculo (~127 arquivos → poucos milhares de chunks). Latência dominada pelo LLM. Script de reindex offline é a estratégia correta de freshness. |
| **Testabilidade** | ✅ (incluir no plano) | Use case + porta + chunker precisam de testes unitários (limites de chunk, filtro por papel, extração de citações, caminhos 503). Fácil via fake `IDocSearchPort`. |
| **UX** | ✅ Adotar (grounding obrigatório) | Helper para todos os usuários é valioso e descobrível, mas precisa ser **claramente distinto** do chat de relatos (rótulo/lugar diferentes). Grounding + citações são requisito de correção, não só de segurança. |

### A tensão central (#1) — o único bloqueador real

As três decisões combinadas (corpus completo + todos os usuários + chat) criam um caminho de divulgação que nenhuma cria sozinha. O `_output/` é material de SDLC interno: descreve **como** o sistema foi construído e **onde** as fraquezas foram consideradas. Um chat semântico é exatamente bom em trazer o chunk que um cidadão curioso (ou adversário) pedir ("quais as vulnerabilidades conhecidas desta plataforma?"). Isso é um rebaixamento de confidencialidade de conteúdo nunca escrito para o usuário final.

**Mitigação barata e recomendada** (não exige relitigar as decisões): tag de `role_visibility` (`public` | `internal`) + `doc_type` em cada chunk no momento da indexação, com **default-deny**, e filtro de query do Chroma por papel do chamador (`where={"role_visibility": ...}`). Para um PoC de curso, uma exclude-list por globs de diretório/arquivo (`security-checklists`, `threat-model`, `_output/check-logs`, internals de planos) é trabalho de ~30 min e remove o risco bloqueador.

## Best practices de RAG aplicáveis (estabelecidas)

- **Chunking por heading com overlap** (~500–800 tokens, pequeno overlap) em vez de doc inteiro: cabe na janela de contexto e produz citações precisas (`source_path#section`).
- **Metadata-filtered retrieval**: filtrar por `role_visibility`/`doc_type` é nativo do Chroma (`where=`) e barato — base da mitigação de segurança.
- **Delimitar chunks recuperados como dado não-confiável** no prompt (defesa contra prompt-injection vinda do próprio corpus markdown) + instrução "use apenas o contexto, não invente".
- **Citar fontes** sempre (`cited_doc_paths`) — grounding verificável reduz alucinação e é requisito de UX.

---

## Recomendações (sumário)

1. **[ALTA] Resolver a Tensão #1 com allow-list curada + metadata `role_visibility`** — não indexar o corpus completo cru numa coleção legível por cidadão. Default-deny: só `product-design/` público + tipos `_output` whitelisted (ex. communications) recebem `public`; security/threat-model/internals de planos/reflections/research ficam `internal`. Filtro Chroma `where` por papel (citizen → só `public`; admin → tudo; agent → tier intermediário). Alternativa explícita: aceitar o risco e registrar como Decisão D-NNN — mas a mitigação barata torna a aceitação desnecessária.

2. **[ALTA] Introduzir um bounded context próprio para docs, sem sobrecarregar a porta de relatos** — novos artefatos: `IDocSearchPort` + `IDocIndexer` (em `domain/repositories/`, com value object `DocChunk{text, source_path, doc_type, section, role_visibility}`); infra `ChromaDocSearchClient` (coleção própria `falagavea_selfdocs`, **reusando o modelo e5 já carregado**); use case `AnswerHelpWithRag` → `HelpAnswer(response, cited_doc_paths)`; `get_doc_search_port()` lazy-singleton em `dependencies.py`; router `POST /nl/help`. A porta de relatos (id → hidrata SQL) não cabe em chunks de doc; reusá-la daria *mais* código (repo falso) e confusão.

3. **[MÉDIA] Chunk por heading markdown com overlap e metadata rica** — `source_path`, `doc_type`, `section_title`, `chunk_index`, `role_visibility` por chunk. Habilita citação precisa e o filtro por papel da Rec #1.

4. **[MÉDIA] Freshness via script de reindex offline** — `scripts/reindex_selfdocs.py` rodado manualmente após mudanças nos artefatos SEJA, espelhando os seed scripts. Hook de filesystem-watch é YAGNI para entrega de curso. Documentar o comando no CLAUDE.md e comunicar na UI ("baseado em docs de <data>").

5. **[MÉDIA] Reusar contrato 503 + rate-limit por usuário + prompt de grounding** — `/nl/help` deve dar 503 quando LLM/doc-search indisponíveis (espelhar `nl.py:45-54`), aplicar o mesmo limiter `slowapi` por usuário de `/nl/filter`, usar system prompt pt-BR endurecido que delimita chunks como dado não-confiável e proíbe invenção, e retornar `cited_doc_paths` para a UI mostrar fontes.

6. **[BAIXA] Testes unitários espelhando `AnswerWithRag`** — limites do chunker, filtro de papel exclui chunks `internal` para citizen, extração de citação, fallback de contexto vazio, caminhos 503. Via fake `IDocSearchPort` (sem Chroma/LLM).

7. **[BAIXA] Verificar e documentar a postura de privacidade** — nota de que, com `FALA_GAVEA_LLM_PROVIDER=anthropic`, chunks de doc (não relatos) vão à nuvem; confirmar que as regras de exclude do indexer descartam padrões de secret (S1) e qualquer arquivo com dado real de cidadão (S2/C1).

## Trade-offs principais

- **Segurança × decisão "corpus completo" (Tensão #1)**: conflito direto. A forma segura de honrar as duas decisões (corpus completo + todos os usuários) é o filtro por `role_visibility` (Rec #1), não indexar tudo cru numa coleção legível por cidadão.
- **C1/nuvem × conveniência (Anthropic)**: sem conflito real — C1 escopa dado de cidadão; self-docs estão fora. Permitir Anthropic para `/nl/help`, mantendo as regras de exclude do indexer.
- **Simplicidade/YAGNI × rigor de arquitetura**: tentador reusar a porta de relatos para poupar arquivos; resolução favorece a porta dedicada (Rec #2) porque o formato id→SQL genuinamente não cabe.

---

## Q&A log

**Q1 (2026-06-26):** chat helper para usuário. O chat acoplado ao sistema acessa um corpus de documentação (que foi gerada neste mesmo projeto, podem ser os planos/researcher/comunications que foram gerados pelo seja + casos de uso e o que foi implementado). O chat é enriquecido com rag desses documentos e é um assistente para a comunicação do que é a plataforma.

**A1:** Trata-se de uma segunda experiência de chat, distinta do `/nl/chat` de relatos: um assistente de metacomunicação/onboarding ancorado por RAG sobre a documentação do próprio projeto. Após esclarecer audiência (todos os autenticados), corpus (SEJA completo + product-design), relação (feature separada com endpoint e coleção próprios) e provider (factory atual, Ollama padrão), a recomendação central é:

- Construir um **bounded context próprio** (`IDocSearchPort`/`IDocIndexer` + `ChromaDocSearchClient` em coleção separada + use case `AnswerHelpWithRag` + `POST /nl/help`), reutilizando o modelo de embedding e o contrato 503/rate-limit existentes — **sem** sobrecarregar a porta de relatos.
- Indexar com **chunking por heading** e metadata rica, **citando as fontes** (`cited_doc_paths`).
- Resolver a tensão de segurança dominante: como cidadãos terão acesso, **não** indexar o corpus interno completo cru — aplicar `role_visibility` (default-deny) + filtro por papel no Chroma, ou no mínimo uma exclude-list de docs sensíveis (security-checklists, threat-model, internals).
- Privacidade: C1 não é violado (docs ≠ dado de cidadão); reusar a factory é adequado, com regras de exclude contra PII/secrets.
- Freshness: script de reindex offline, adequado ao PoC.

Recomendações priorizadas listadas acima (2 ALTA, 3 MÉDIA, 2 BAIXA).
