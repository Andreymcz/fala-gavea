# Reflection 000171 | 2026-06-25 19:14 UTC | IA sugerir topicos para relatos sem topico

## Artifacts reflected on

Free-form — no artifact anchor.

## Summary

Exploração prospectiva sem artefato de referência. A questão surgiu da observação de que a plataforma e os dados sintéticos assumem que todos os relatos já possuem tópicos definidos. A ideia central é introduzir a capacidade da IA de sugerir tópicos para relatos que não os têm, usando colunas especiais na tabela de dados (com símbolo indicador de conteúdo gerado por IA) — análogo ao que já existe com tags.

## Reflection

"nao sei ainda, quero explorar como podemos introduzir no codebase atual sem muita fricção"

### Notas de exploração (registradas pelo agente a partir da conversa)

**O problema que motivou a reflexão:**

Hoje, `seed_relatos_fala_gavea_5k.csv` e a lógica de ingestão assumem que tópicos existem. Relatos sem tópico simplesmente ficam sem classificação semântica — não há caminho para a IA preencher esse campo de forma assistida.

**O que já existe e pode servir de analogia:**

- O modelo `Relato` já tem `tags` (lista de strings) — geradas/editadas por humano ou IA
- O campo `topico` (se existir) ou equivalente seria análogo: string categórica gerada por IA quando ausente

**Possíveis pontos de entrada de baixa fricção:**

1. **Na ingestão/seed** — o script de seed poderia chamar um classificador leve (embeddings + ChromaDB) para inferir tópico quando o CSV não fornece um
2. **No endpoint de criação de relato** — um use case `SuggestTopicUseCase` chamado assincronamente após persistência, que preenche o campo se vazio
3. **No frontend** — ao criar um relato sem tópico, o form poderia exibir sugestões geradas pelo backend antes do submit final

**Marcador de conteúdo IA (ideia de dados):**

A sugestão de usar um símbolo especial (ex.: prefixo `ai:` ou coluna `topico_ia_score`) cria uma distinção auditável entre tópicos declarados pelo cidadão e tópicos inferidos pela IA. Isso tem valor para transparência e para treino futuro.

**O que ainda não está claro:**

- Se `topico` é um campo livre (string) ou enumerado — isso muda muito o custo de inferência
- Se a sugestão deve ser apresentada ao cidadão para confirmação, ou aplicada silenciosamente (implicações de UX e confiança)
- Onde no clean-architecture atual esse use case "assistido" mora (application layer? infrastructure layer chamado por trigger?)

## Follow-ups

- Verificar o schema atual de `Relato` — existe campo `topico`? É string livre ou FK para tabela de tipos?
- Avaliar se `ChromaClient` existente pode servir como base para o classificador de tópicos (zero-shot via similaridade com tópicos conhecidos)
- Decidir se a sugestão é síncrona (bloqueia criação) ou assíncrona (enriquecimento posterior)
- Definir convenção de marcador IA nos dados (prefixo, flag booleano, score de confiança)
- Considerar `/research` para mapear o espaço de design antes de `/plan`
