# Schema CSV — Relatos Fala Gávea

Cada CSV neste diretório é ingerido por `scripts/seed_relatos.py`.
Sugestão: um CSV por **eixo de conexão temática** (ver abaixo).

## Colunas obrigatórias

| Coluna | Tipo | Exemplo |
|--------|------|---------|
| id_cidadao | string | citizen01 |
| texto_relato | string | Poste apagado na Rua X causando risco de assalto |
| latitude | float | -22.9651 |
| longitude | float | -43.2180 |
| data | string ISO 8601 | 2025-09-14 |
| topico | string | Iluminacao publica |

## Tópicos válidos

Iluminacao publica, Transito e mobilidade, Vandalismo,
Espaco publico, Lixo e conservacao, Seguranca e circulacao,
Conflito social, Outro

## Eixos de conexão temática (sugestão de CSVs)

Cada CSV pode explorar um eixo. O `texto_relato` deve deixar claro
a conexão — o texto é o dado que alimenta a busca semântica e o chat NL.

| Arquivo sugerido | Eixo | Tópico primário |
|-----------------|------|----------------|
| `saneamento_saude.csv` | Lixo/esgoto → risco de doença (leptospirose, dengue, cólera) | Lixo e conservacao |
| `iluminacao_seguranca.csv` | Postes apagados → assaltos, medo de circular à noite | Iluminacao publica |
| `espaco_conflito.csv` | Praças/parques degradados → uso de drogas, brigas, abandono | Espaco publico |
| `transito_segviaria.csv` | Semáforos/buracos → acidentes, atropelamentos | Transito e mobilidade |
| `conflito_saudemental.csv` | Conflito social → ansiedade, insônia, saúde mental de moradores | Conflito social |
| `infra_acessibilidade.csv` | Calçadas/entulho → exclusão de idosos, cadeirantes, crianças | Espaco publico |
| `multiplo.csv` | Problemas sobrepostos no mesmo ponto (ex: lixo + sem luz + esgoto) | Outro |

## Bounding box Gávea

lat: -22.975 … -22.953  |  lon: -43.235 … -43.205

## Datas

Qualquer data dentro do intervalo 2025-06-18 … 2026-06-18.

## Cidadãos de teste

citizen01 (citizen01@gavea.br) — pode repetir em todas as linhas.

## Dica para o texto_relato

O texto é o campo mais importante para a busca semântica.
Escreva em voz de cidadão, mencione a conexão explicitamente:
  ❌ "Lixo acumulado na rua."
  ✓  "Lixo acumulado ha semanas na Rua X. Ja apareceram ratos; temo
      surto de leptospirose — criancas brincam perto todos os dias."
