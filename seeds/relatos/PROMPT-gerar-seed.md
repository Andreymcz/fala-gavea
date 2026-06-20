# Prompt — gerar CSV de Seed de Relatos (fala-gavea)

Cole o bloco abaixo na base de conhecimento (kb-qa) ou em qualquer LLM com acesso
a este repositório para gerar um CSV importável pelo painel admin
(`POST /admin/seed/relatos`, card "Seed de Relatos").

O cabeçalho usa `user_id` (canônico); o endpoint também aceita `id_cidadao` como
alias. Apenas `user_id` é obrigatório — as demais colunas têm fallback automático,
mas o prompt instrui o modelo a preenchê-las para gerar dados mais úteis.

---

```text
# Tarefa: gerar CSV de Seed de Relatos para o fala-gavea

Você é um gerador de dados de seed para o sistema **fala-gavea** (demandas de
cidadãos sobre segurança urbana na Gávea, Rio de Janeiro). Use como matéria-prima
os comentários reais disponíveis neste repositório e produza um CSV de relatos
fictícios, porém realistas, prontos para importar pelo painel admin
(POST /admin/seed/relatos).

## Fontes a consultar neste repositório
- `data/sample-gavealab.csv` (colunas: id, comment, territory)
- `data/sample-gavealab-diagnostico.csv` (colunas: author_id, territory_level,
  territory_name, text)
- `seeds/relatos/SCHEMA.md` (tópicos válidos, bounding box, eixos temáticos)

Transforme os comentários dessas fontes em relatos na **voz de um cidadão**,
mantendo o tema, mas reescrevendo para soar como uma demanda concreta sobre um
ponto da Gávea. Não copie literalmente: parafraseie e enriqueça.

## Formato de saída (OBRIGATÓRIO)
- Apenas o conteúdo CSV, **sem** texto extra, sem markdown, sem cercas de código.
- Codificação UTF-8. Separador vírgula. Campos com vírgula/quebra de linha
  entre aspas duplas.
- Primeira linha exatamente este cabeçalho:

user_id,texto_relato,latitude,longitude,data,topico,urgency

- Gere **40 linhas** de dados (ajuste se eu pedir outra quantidade).

## Regras por coluna
- **user_id** (única coluna obrigatória): identificador curto e estável do autor,
  ex.: `citizen01`, `c0007`. Reutilize o mesmo user_id em várias linhas para
  simular cidadãos recorrentes (use ~10 a 15 cidadãos distintos no total). Pode
  derivar de `author_id`/`id` das fontes. Nunca deixe vazio.
- **texto_relato**: 1 a 3 frases, voz de cidadão, mencionando explicitamente o
  problema e, quando fizer sentido, a consequência (ex.: poste apagado → medo de
  assalto; lixo → risco de leptospirose). Cite ruas/pontos da Gávea quando couber
  (ex.: Parque da Cidade, Praça Santos Dumont, Rua Marquês de São Vicente).
- **latitude / longitude**: ponto dentro do bounding box da Gávea —
  lat entre **-22.975 e -22.953**, lon entre **-43.235 e -43.205**, 6 casas
  decimais. (Se deixar em branco, o sistema gera um ponto aleatório na Gávea —
  prefira preencher.)
- **data**: ISO `YYYY-MM-DD`, distribuída no intervalo **2025-06-18 a 2026-06-18**.
  (Vazio = momento da importação.)
- **topico**: exatamente um destes valores (texto idêntico):
  `Iluminacao publica`, `Transito e mobilidade`, `Vandalismo`, `Espaco publico`,
  `Lixo e conservacao`, `Seguranca e circulacao`, `Conflito social`, `Outro`.
  Escolha o tópico que melhor casa com o texto. (Tópico inexistente seria
  criado automaticamente, mas use esta lista para manter consistência.)
- **urgency**: um de `alta`, `media`, `baixa`. Heurística: risco imediato à vida/
  segurança (assalto, atropelamento, esgoto a céu aberto) → `alta`; incômodo
  relevante mas sem risco iminente → `media`; estético/menor → `baixa`. (Vazio
  assume `media`.)

## Qualidade
- Varie tópicos, urgências, localizações e autores — evite repetição mecânica.
- Mantenha coerência entre texto, tópico e urgência.
- Não invente colunas além das sete do cabeçalho.

Gere agora o CSV.
```
