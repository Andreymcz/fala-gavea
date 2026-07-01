# Research 000193 | fala-gavea | 2026-07-01 15:01 UTC | Conteúdo sensível / PII nos artefatos SEJA
tags: security, privacy, publishing, seja-artifacts, compliance

## User brief

> contúdo sensível nos artefatos SEJA deste repositorio. algumas skills podem ter referenciado conversas privadas de whatsapp por ex. pesquisa por nomes que possam identificar pessoas.
> Andrey, Mauro, Natali, Julia, SHeila, Herbert

## Agent interpretation

Auditar todos os artefatos gerados pela harness SEJA (e demais arquivos versionados) em busca de conteúdo sensível ou que identifique pessoas reais: (a) trechos de conversas privadas de WhatsApp que alguma skill possa ter capturado; (b) nomes de pessoas reais — a equipe (Andrey, Mauro, Natali, Julia, Herbert) e o nome extra "Sheila"; (c) qualquer PII colateral (telefone, CPF, e-mail, caminhos locais com nome de usuário). Objetivo prático: saber o que existe e o que deve ser removido antes de eventual publicação (repo público / entrega ao curso / pipeline `/publish`).

## Escopo varrido

- `_output/` inteiro (briefs, telemetry, plans, communication, research-logs, reflections, qa-logs, briefs-index)
- `product-design/` (constitution, ux-research-results, product-design-as-intended/-as-coded)
- `.claude/` (skills) e `.claude/worktrees/` (cópias não versionadas)
- `data/` e `seeds/` (CSVs e prompt gerador de seed)
- `README.md`, `CLAUDE.md`, `docs/`
- Sweep repo-wide via `git grep` (arquivos versionados) + Grep (working tree, incl. worktrees)

## Achados

### 1. Conversas privadas de WhatsApp — NADA encontrado ✓

Todas as ~7 menções a "WhatsApp" são **contexto de domínio / persona**, não transcrições:
- `product-design/project/ux-research-results.md` (personas: cidadão/agente usam apps como WhatsApp; agente recebe demandas por grupos de WhatsApp)
- `product-design/project/product-design-as-intended.md:231` (problemas "ficam no boca-a-boca, nos grupos de WhatsApp")
- `_output/research-logs/research-000186`, `_output/communication/.../*-academics.*`, `_output/reflections/reflection-000149` (todos citando WhatsApp como canal informal de reporte)

Nenhum print, áudio, transcrição ou citação de conversa privada foi encontrado. A preocupação central do brief é **infundada** para este repositório.

### 2. "Sheila" — NÃO aparece em nenhum artefato ✓

`\bsheila\b` (case-insensitive, working tree inteiro incl. worktrees) retorna **apenas** a entrada de brief que acabei de escrever para esta própria pesquisa (`_output/briefs.md:3`). Não há nenhuma pessoa "Sheila" referenciada em código, docs, artefatos SEJA ou seed data.

### 3. Nomes da equipe — só atribuição de autoria (sensibilidade baixa)

Andrey, Mauro, Julia, Herbert, Natali aparecem **exclusivamente como crédito/autoria** — primeiros nomes, sem sobrenome, sem contato, sem dado privado:
- `product-design/project/constitution.md:5` e `README.md:6` — "Team/Equipe: Andrey, Mauro, Julia, Herbert, Natali"
- `_output/communication/**/*-academics.*` + `docs/*-academics.*` — linha de crédito da equipe nos relatórios acadêmicos
- `_output/telemetry.jsonl`, `_output/briefs*.md` — briefs de skill (ex.: "academic final-report material for Julia (ACD, pt-BR)")
- `_output/plans/plan-000085*` e `seeds/relatos/PROMPT-gerar-seed.md` — referências a "colaborador Herbert" (quem coletou os relatos-fonte)

Isso é esperado para uma entrega de curso avaliada; os autores se auto-identificam. Nenhum sobrenome, e-mail pessoal, telefone ou CPF associado.

### 4. "Relatos reais coletados pelo Herbert" — de-identificados, não são PII ✓

`seeds/relatos/PROMPT-gerar-seed.md` (§ "Banco de relatos-fonte (Herbert) — texto integral", ~linhas 100-260) embute relatos reais de campo sobre segurança urbana numa comunidade da Gávea. **Estão anonimizados**: usam descritores genéricos ("Idoso relata", "Universitária relata", "Homem trans relata", "Moradores relatam") — sem nomes, endereços, telefones ou qualquer identificador. É matéria-prima de pesquisa legítima e já de-identificada.

Ressalva (risco residual baixo): alguns relatos descrevem situações sensíveis e recentes numa comunidade real (tentativas de violência sexual, operações policiais, recrutamento por facções, tiroteios). Como estão generalizados e sem identificação individual, não configuram PII, mas convém tratá-los como dados sensíveis de pesquisa se o repo for público.

### 5. ACHADO REAL — vazamento de caminho local com nome de usuário (MÉDIO)

`_output/plans/plan-000082-progress.md` (**versionado no git**) contém, nas linhas 7 e 24, o caminho absoluto:

```
c:\Users\arodrigues\Pesquisa\doutourado\2026.1\INF2921\inf2921-grupo-c\fala-gavea
```

Vaza: o usuário do SO `arodrigues` (identifica Andrey Rodrigues), o status acadêmico ("doutourado" = doutorado) e a estrutura de diretórios pessoal. É a **única** ocorrência de `arodrigues`/`doutourado` em todo o repo. Baixo risco de segurança, mas é exatamente o tipo de fragmento identificador a limpar antes de publicar. Como `_output/` é versionado, também está no histórico git.

### 6. Sem outros vazamentos de PII ✓

Buscas por CPF (`\d{3}.\d{3}.\d{3}-\d{2}`), telefones BR, `@gmail/@hotmail/@outlook`, `matrícula`, `andreymcz`/`arodrigues` em `_output/` não retornaram nada além do achado 5. Seed CSVs usam IDs anônimos (`citizen060`, ...), sem nomes. Personas são anônimas (R-P-001/002/003).

## Q&A log

**1. (verbatim)** contúdo sensível nos artefatos SEJA deste repositorio. algumas skills podem ter referenciado conversas privadas de whatsapp por ex. pesquisa por nomes que possam identificar pessoas. Andrey, Mauro, Natali, Julia, SHeila, Herbert

**Resposta:** Varredura completa do working tree e dos arquivos versionados. Resultado: **nenhuma conversa privada de WhatsApp** foi capturada em artefato (todas as menções a WhatsApp são contexto de domínio/persona); **"Sheila" não existe** em nenhum artefato; os nomes da equipe aparecem só como atribuição de autoria (primeiros nomes, sem PII); os "relatos reais do Herbert" estão de-identificados. O único conteúdo a corrigir é o vazamento do caminho local `c:\Users\arodrigues\...\doutourado\...` em `_output/plans/plan-000082-progress.md` (versionado). Detalhe e recomendações abaixo.

## Perspectivas avaliadas

Por ser uma auditoria factual (e não uma decisão de design com trade-offs), não acionei o `research-reviewer`; apliquei diretamente as perspectivas pertinentes.

- **Segurança / Privacidade:** o repo está essencialmente limpo de PII. Único item concreto é o caminho local do achado 5. Os relatos-fonte são dados sensíveis mas de-identificados.
- **Prontidão para publicação (`/publish`, repo público, entrega ao curso):** decidir política de atribuição de nomes (manter vs. anonimizar para avaliação cega) e limpar o caminho local antes de tornar público.
- **Governança de dados de pesquisa:** os relatos coletados em campo já seguem boa prática (anonimização por descritor). Bom manter uma nota de proveniência se publicados.

## Recommendations summary

- **[MÉDIO] R1 — Limpar o caminho local versionado.** Substituir `c:\Users\arodrigues\Pesquisa\doutourado\2026.1\INF2921\inf2921-grupo-c\fala-gavea` por um placeholder (`<repo-root>`) ou caminho relativo em `_output/plans/plan-000082-progress.md` (linhas 7 e 24). Também está no histórico git — para um repo de curso, corrigir no working tree basta; só considere reescrita de histórico se o repo for realmente publicado.
- **[BAIXO] R2 — Definir política de atribuição de nomes antes de publicar.** Os primeiros nomes da equipe estão em constitution/README/relatórios acadêmicos. Manter é adequado (autores se identificam). Se a avaliação for cega ou o repo for público, decidir conscientemente por manter ou anonimizar esses arquivos.
- **[BAIXO/INFO] R3 — Tratar os relatos-fonte do Herbert como dados sensíveis de pesquisa.** Já de-identificados; nenhuma ação obrigatória. Se o repo for público, adicionar uma nota de que são relatos anonimizados coletados para fins de design.
- **[INFO] R4 — Preocupação original resolvida.** Não há conversas privadas de WhatsApp nem qualquer "Sheila" nos artefatos; a captura de conteúdo privado por skills não ocorreu neste repositório.
