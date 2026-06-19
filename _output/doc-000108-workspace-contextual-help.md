---
doc_type: contextual-help
freshness: every-release
diataxis: how-to
plan: 000104
generated: 2026-06-19
---

# Workspace — Ajuda Contextual

> Microcopy de auto-explicação por visão — documentado aqui para referência de design e para futura integração em tela de ajuda.

## O que posso fazer aqui?

O **Workspace de Relatos** é o painel principal do Fala, Gávea. Você decide como explorar os relatos de segurança registrados:

- **Filtre** pelo painel esquerdo: tipo de problema, urgência, status, período, ou busca semântica (IA).
- **Alterne visões** na barra superior: escolha quantas visões quiser ativas ao mesmo tempo.
- **Selecione relatos** na Tabela ou no Mapa para criar encaminhamentos (agentes/admin).

## Visões disponíveis

| Visão | Quem vê | Auto-explicação |
|-------|---------|-----------------|
| **Mapa** | Todos | Veja os relatos no mapa da Gávea |
| **Tabela** | Todos | Liste e selecione relatos para encaminhar |
| **Tópicos** | Agente / Admin | Temas emergentes no subconjunto filtrado (IA) |
| **Similares** | Todos | Relatos parecidos com um relato-semente |
| **Chat** | Agente / Admin | Pergunte sobre os relatos em linguagem natural (IA) |

## Como usar cada visão

### Mapa
1. O mapa exibe todos os relatos que correspondem ao filtro ativo (marcadores agrupados).
2. Clique em um marcador para ver os detalhes e selecionar o relato (agentes).
3. Para filtrar por área, clique em **Desenhar área**, clique duas vezes no mapa para definir os cantos do retângulo, e o filtro de área é aplicado automaticamente. Clique **Limpar área** para remover.

### Tabela
1. As linhas exibem todos os relatos filtrados, com urgência (▲ Alta / ● Média / ▼ Baixa), status e data.
2. Clique em uma linha (ou na caixa de seleção) para selecionar o relato.
3. Clique em **Similares** em qualquer linha para explorar relatos parecidos na visão Similares.

### Tópicos *(Agente / Admin)*
1. Mostra os temas que emergem dos relatos no subconjunto filtrado, calculados por IA (BERTopic).
2. Cada tópico lista os termos principais e a quantidade de relatos.
3. Se a IA não estiver disponível, aparece a mensagem "Análise de tópicos indisponível".

### Similares
1. Clique em **Similares** na linha de um relato da Tabela (ou em um botão de relato citado no Chat).
2. A visão busca relatos parecidos em **toda a base**, independente do filtro ativo.
3. A faixa "Similares em toda a base, fora do filtro" fica sempre visível para lembrar que o conjunto não é filtrado.

### Chat *(Agente / Admin)*
1. Digite uma pergunta sobre os relatos em linguagem natural e pressione Enter ou **Enviar**.
2. O assistente responde com base nos relatos semânticos mais relevantes e cita os relatos usados (clique nas citações para explorá-los na visão Similares).
3. Se a IA não estiver disponível, aparece a mensagem "Assistente indisponível".

## Como saberei que minha ação funcionou?

- **Filtro aplicado**: o contador de relatos no painel esquerdo atualiza instantaneamente; usuários de leitores de tela ouvem o anúncio.
- **Relatos selecionados**: a barra "N relatos selecionados" aparece na parte inferior (agentes/admin).
- **Encaminhamento criado**: notificação de confirmação aparece e a seleção é limpa automaticamente.
- **Visão ligada/desligada**: o botão da visão altera seu estado (pressionado/solto); a visão aparece ou desaparece da grade.

## Restrições

- **Tópicos** e **Chat** requerem perfil de Agente ou Admin.
- **Tópicos** requer pelo menos 3 relatos no subconjunto filtrado (`min_docs=3`).
- **Busca semântica**: mostra no máximo 50 relatos mais relevantes; quando esse limite é atingido, um aviso aparece no painel de filtro.
- **IA (Tópicos/Similares/Chat)**: podem estar indisponíveis se o provedor semântico/LLM não estiver configurado — o workspace continua funcional com Mapa e Tabela.

## Localization

Toda a microcopy está em pt-BR inline nos componentes. Para internacionalização futura: extrair strings para `frontend/src/i18n/locales/pt-BR.json`.
