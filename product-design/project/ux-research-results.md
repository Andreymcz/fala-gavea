# UX RESEARCH RESULTS — fala-gavea

<!-- maintained-by: human (designer/researcher); Human (markers) classification since SEJA 2.8.2 -->

---

## 1. Personas

### Persona Inventory

| ID | Name | Role / Archetype | Goals |
|----|------|-----------------|-------|
| R-P-001 | Cidadão | Morador da Gávea / Usuário do sistema | Registrar problema urbano sem burocracia; confirmar que foi recebido |
| R-P-002 | Agente Público | Servidor municipal responsável por triagem de demandas | Explorar demandas eficientemente; criar encaminhamentos rastreáveis; reduzir tempo de triagem |
| R-P-003 | Administrador | Gestor do sistema / TI municipal | Manter taxonomia de tipos de problema atualizada; gerenciar usuários |

### R-P-001: Cidadão

> **Role / Archetype:** Morador da Gávea que usa smartphone para registrar problemas urbanos.
>
> **Bio:** Morador do bairro da Gávea, Rio de Janeiro. Usa smartphone Android ou iOS para comunicação. Tem familiaridade básica com apps de celular. Frequentemente observa problemas urbanos (postes apagados, buracos, lixo) mas não sabe como ou onde reportar oficialmente.
>
> **Goals:**
> - G-001: Registrar um problema urbano de forma rápida, sem burocracia, diretamente do local onde está.
> - G-002: Confirmar que o registro foi recebido pelo poder público e acompanhar o status.
>
> **Key Frustrations:**
> - Não saber para onde ligar ou enviar email para reportar um problema específico.
> - Formulários burocráticos que pedem dados que o cidadão não tem (número do processo, código do logradouro, etc.).
> - Falta de feedback após reportar: "reportei e nunca soube o que aconteceu".
>
> **Relevant Context:**
> - Technical proficiency: novice a intermediate (sabe usar apps de redes sociais, maps, WhatsApp)
> - Usage frequency: occasional (ao observar um problema)
> - Domain knowledge: usuário do espaço urbano; sem conhecimento técnico da gestão municipal

---

### R-P-002: Agente Público

> **Role / Archetype:** Servidor da Prefeitura do Rio responsável pela triagem e encaminhamento de demandas urbanas da Gávea.
>
> **Bio:** Servidor municipal com foco na Região Administrativa da Gávea. Utiliza desktop/notebook no escritório. Recebe demandas de múltiplos canais (telefone, email, grupos de WhatsApp, redes sociais, 1746) e precisa organizá-las e encaminhá-las para os órgãos executores corretos (RioLuz, COMLURB, CET-Rio, etc.).
>
> **Goals:**
> - G-001: Identificar rapidamente quais demandas são prioritárias e similares para agrupá-las.
> - G-002: Criar encaminhamentos formais e rastreáveis para os órgãos responsáveis.
> - G-003: Reduzir o tempo gasto em triagem manual de demandas repetidas.
>
> **Key Frustrations:**
> - Receber o mesmo tipo de demanda dezenas de vezes sem poder agrupá-las automaticamente.
> - Não ter visão geoespacial das demandas (não saber que 10 relatos de postes apagados estão no mesmo quarteirão).
> - Ferramentas de back-office lentas e pouco intuitivas.
>
> **Relevant Context:**
> - Technical proficiency: intermediate (usa sistemas de back-office, Excel, email)
> - Usage frequency: daily (durante turno de trabalho)
> - Domain knowledge: conhece bem a estrutura municipal, quais órgãos são responsáveis por quê, sazonalidades de demandas

---

### R-P-003: Administrador

> **Role / Archetype:** Responsável pela configuração e gestão do sistema fala-gavea.
>
> **Bio:** Perfil técnico ou gerencial na prefeitura com acesso de administrador ao sistema. Configura os tipos de problema disponíveis para os cidadãos, pode promover usuários entre roles, e monitora o funcionamento do sistema.
>
> **Goals:**
> - G-001: Manter a lista de tipos de problema atualizada e relevante para a realidade da Gávea.
> - G-002: Garantir que apenas agentes autorizados tenham acesso às funcionalidades de encaminhamento.
>
> **Key Frustrations:**
> - Precisar de um desenvolvedor para adicionar um novo tipo de problema.
> - Sem visibilidade sobre qual agente criou qual encaminhamento.
>
> **Relevant Context:**
> - Technical proficiency: intermediate a expert
> - Usage frequency: occasional (configuração e manutenção)
> - Domain knowledge: entende a taxonomia de problemas urbanos e a estrutura de órgãos

---

## 2. Problem Scenarios

### R-PS-001: Poste apagado — cidadão sem canal de reporte

- **Persona:** R-P-001 (Cidadão)
- **Goals:** G-001, G-002
- **Setting:** Noite de segunda-feira, cidadão caminha pela rua Marquês de São Vicente na Gávea e nota que dois postes estão apagados, criando zona escura no trecho.

O cidadão para na frente dos postes apagados e pega o celular. Sabe que precisa reportar o problema — "isso é perigoso, especialmente à noite" — mas não sabe para onde. Tenta o 1746 (central de atendimento da prefeitura), fica em fila de espera por 8 minutos. Desiste. Vai ao Google e pesquisa "reportar poste apagado gávea rio de janeiro". Encontra um formulário da CET-Rio que parece errado (poste é RioLuz, não trânsito). Vai ao WhatsApp da associação de moradores, manda mensagem, mas ninguém responde à noite.

No dia seguinte, decide não reportar formalmente. Fala com o vizinho que também notou o problema. "Alguém já deve ter reportado." O problema continua sem solução por semanas.

> Contexto de uso indevido: cidadão poderia usar o sistema para registrar relatos falsos ou spam. Mitigação: autenticação obrigatória para registro + moderação futura.

---

### R-PS-002: Agente sem visão geoespacial das demandas

- **Persona:** R-P-002 (Agente Público)
- **Goals:** G-001, G-003
- **Setting:** Terça-feira de manhã, agente começa turno e tem 47 demandas não triadas na fila.

O agente abre o sistema de back-office e vê uma lista de 47 demandas em texto, sem mapa, sem clustering. Percorre linha por linha. Identifica na 3ª, na 12ª e na 31ª demandas que parecem ser sobre o mesmo problema ("poste apagado na Marquês de São Vicente") mas usam palavras diferentes: "luz apagada", "poste sem luz", "rua escura". Sem busca semântica, só percebe a relação porque leu os três textos manualmente.

Gasta 45 minutos para triagem. Cria três encaminhamentos separados para a RioLuz porque não percebeu que os três relatos eram do mesmo trecho da rua. A RioLuz recebe três tickets para o mesmo problema, mandando três equipes diferentes ao mesmo local.

---

## 3. Cross-Reference Map

| Artifact ID | Artifact Title | Design Artifact | Relationship |
|-------------|---------------|----------------|-------------|
| R-P-001 | Cidadão | product-design-as-intended EMT 1.1 | Feeds |
| R-P-002 | Agente Público | product-design-as-intended EMT 1.1 | Feeds |
| R-P-003 | Administrador | product-design-as-intended EMT 1.1 | Feeds |
| R-PS-001 | Poste apagado — sem canal de reporte | product-design-as-intended §13 US-001 | Informa |
| R-PS-002 | Agente sem visão geoespacial | product-design-as-intended §13 US-002, US-003 | Informa |

---

## 4. Goals Summary

| Persona | Goal ID | Goal Description |
|---------|---------|-----------------|
| R-P-001 | G-001 | Registrar problema urbano de forma rápida e sem burocracia |
| R-P-001 | G-002 | Confirmar recebimento e acompanhar status do relato |
| R-P-002 | G-001 | Identificar e agrupar demandas similares rapidamente |
| R-P-002 | G-002 | Criar encaminhamentos formais e rastreáveis |
| R-P-002 | G-003 | Reduzir tempo de triagem manual |
| R-P-003 | G-001 | Manter taxonomia de tipos de problema atualizada |
| R-P-003 | G-002 | Controlar acesso de agentes ao sistema |

---

## 5. Discovered User Journeys

_Nenhuma sessão de pesquisa formal conduzida até o momento. Journeys descobertos serão documentados aqui quando pesquisa de campo for realizada. Ver `product-design/project/product-design-as-intended.md §15` para journeys projetados baseados nos casos de uso do roadmap-000071._

---

## CHANGELOG

2026-06-17 | R-P-001 | added | - | Persona Cidadao criada via /design roadmap 1 item 1c
2026-06-17 | R-P-002 | added | - | Persona Agente Publico criada via /design roadmap 1 item 1c
2026-06-17 | R-P-003 | added | - | Persona Administrador criada via /design roadmap 1 item 1c
2026-06-17 | R-PS-001 | added | - | Problem scenario: cidadao sem canal de reporte
2026-06-17 | R-PS-002 | added | - | Problem scenario: agente sem visao geoespacial
