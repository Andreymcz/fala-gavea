# Communication 000126 | CLT | 2026-06-21 15:31 UTC | Clients

**Produto:** Fala, Gavea! -- Sistema de demandas de cidadaos para seguranca urbana  
**Destinatarios:** Professores coordenadores INF2921/CIS2114 e partes interessadas em seguranca urbana  
**Data:** 21 de junho de 2026  
**Fase atual:** PoC/MVP entregue para avaliacao academica (2026.1)  
**Equipe:** Andrey, Mauro, Julia, Herbert, Natali

---

## 1. Alinhamento com a Visao do Produto

O produto que voces comissionaram responde a uma necessidade real e documentada: cidadaos do bairro da Gavea (Rio de Janeiro) nao tinham um canal eficiente para registrar problemas de seguranca urbana, e agentes publicos nao contavam com ferramentas para organizar e encaminhar essas demandas de forma sistematica.

O Fala, Gavea! foi construido com tres objetivos centrais, todos derivados das diretrizes do curso e do contexto de seguranca urbana:

| Objetivo comissionado | O que foi entregue |
|---|---|
| Canal de registro para cidadaos | Formulario web com mapa interativo, tipo de ocorrencia, nivel de urgencia e descricao textual |
| Ferramenta de gestao para agentes publicos | Fluxo completo de encaminhamento com rastreamento de status por orgao responsavel |
| Exploracao assistida por IA | Busca semantica, agrupamento de temas, relatos similares e chat em linguagem natural para agentes |

O produto esta alinhado com a visao comissionada. Todos os tres fluxos de usuario definidos no escopo original -- registro pelo cidadao, encaminhamento pelo agente e exploracao por IA -- foram implementados de ponta a ponta.

---

## 2. Status de Entrega

### O que foi construido

**Para o cidadao:**
- Registro de ocorrencias com localizacao geografica (mapa interativo Leaflet + coordenadas lat/lon)
- Classificacao por tipo de problema e nivel de urgencia (alta / media / baixa)
- Autenticacao segura com perfil de cidadao

**Para o agente publico:**
- Painel de trabalho com 5 visoes: mapa de ocorrencias, tabela filtrada, agrupamento de topicos, relatos similares e chat NL
- Gestao de encaminhamentos com ciclo de vida completo: `aguardando_solucao` -> `solucao_em_andamento` -> `finalizado`
- Ferramentas de administracao: importacao em massa via CSV, gestao de banco de dados

**Infraestrutura e seguranca:**
- Autenticacao JWT com tres papeis (cidadao / agente / admin)
- Validacao de entrada em todas as camadas
- Conteiner Docker + deploy na nuvem Railway com volume de dados persistente

**IA embutida:**
- Busca semantica sobre relatos (ChromaDB + sentence-transformers)
- Descoberta de relatos similares
- Agrupamento de temas por TF-IDF
- Assistente de chat em linguagem natural (Ollama, modelo qwen3:8b, opcional)

### O que vem a seguir (fora do escopo do PoC atual)

Os itens abaixo nao fazem parte da entrega avaliada, mas foram identificados como proximos passos naturais para um produto em producao:

- Notificacoes em tempo real para cidadaos (atualizacoes de status)
- Suporte a multiplos idiomas (sistema atual exclusivamente em pt-BR)
- Integracao com sistemas de gestao municipal existentes
- Painel de indicadores para gestores (metricas agregadas por tipo, regiao, urgencia)

### Riscos conhecidos e posicionamento honesto

| Restricao | Impacto | Posicionamento |
|---|---|---|
| SQLite como banco de dados | Adequado para PoC; limitado para escala municipal real | Migracao para PostgreSQL e o proximo passo tecnico se o produto for para producao |
| Ollama (LLM local) opcional | Chat NL retorna 503 gracioso se o servico nao estiver disponivel | Busca semantica e topicos funcionam independentemente do LLM |
| Sem notificacoes em tempo real | Cidadao nao e alertado automaticamente sobre mudancas de status | Requer enquete ativa ou email -- identificado como lacuna para v2 |
| Escopo geografico fixo (Gavea) | Dados de localizacao e contexto calibrados para o bairro | Expansao para outros bairros requer configuracao de contexto |

---

## 3. Evidencias de Resultado

### Cobertura funcional dos fluxos comissionados

| Fluxo | Status | Observacao |
|---|---|---|
| Cidadao registra ocorrencia com localizacao | Entregue | Mapa interativo, validacao de coordenadas, todos os campos |
| Agente visualiza e filtra demandas | Entregue | 5 visoes complementares no painel de trabalho |
| Agente cria e atualiza encaminhamento | Entregue | Ciclo de vida completo com rastreamento de orgao |
| Busca semantica por texto livre | Entregue | ChromaDB + sentence-transformers, pt-BR |
| Agente explora relatos similares | Entregue | Descoberta automatica por proximidade semantica |
| Chat NL para exploracao | Entregue (opcional) | Funciona com Ollama local; sistema degrada graciosamente sem ele |
| Admin importa dados via CSV | Entregue | Ferramenta de carga em massa disponivel |
| Autenticacao e controle de acesso | Entregue | JWT com 3 papeis, sem permissoes cruzadas |

### Qualidade tecnica

- Arquitetura limpa implementada: separacao entre dominio, aplicacao, infraestrutura e apresentacao
- Cobertura de testes: suite pytest (backend) + Vitest (frontend)
- Deploy reproduzivel: Dockerfile + variavel de ambiente, sem segredos embutidos
- Frontend moderno: React 18 + TypeScript + Vite, build estatico servido pelo FastAPI

---

## 4. Mensagem Central (versao em linguagem simples)

O produto que voces comissionaram foi construido e funciona. Um cidadao da Gavea pode abrir o sistema, marcar no mapa onde viu um problema de seguranca, descrever o que aconteceu e enviar -- em menos de dois minutos. Um agente publico pode ver todas as demandas no mapa, buscar por palavras, encontrar relatos parecidos, agrupar por tema e conversar com um assistente de IA para entender o que esta acontecendo no bairro. Quando decide agir, cria um encaminhamento para o orgao responsavel e acompanha o status ate a resolucao.

O sistema foi projetado para ser honesto sobre o que pode e o que nao pode fazer: se o assistente de chat nao estiver disponivel, o sistema avisa e continua funcionando. Se um dado obrigatorio nao foi preenchido, o sistema rejeita com mensagem clara. Se um usuario tenta acessar o que nao e seu, o sistema bloqueia.

Para o contexto academico deste curso, o produto demonstra os principios de design de sistemas de IA em producao: separacao de responsabilidades, degradacao gracosa, autenticacao por papel, e IA como ferramenta de apoio -- nao como substituta do julgamento humano.

---

## 5. Proximas Decisoes que Dependem de Voces

As questoes abaixo nao sao tecnicamente complexas, mas requerem decisao dos comissionadores antes de qualquer evolucao do produto:

1. **Continuidade apos o curso:** O sistema sera descontinuado ao fim do semestre ou ha interesse em manter o deploy para uso real na Gavea?
2. **Dados reais vs. dados de demonstracao:** O banco atual contem dados sinteticos para avaliacao. Uma implantacao real exige politica de privacidade e protecao de dados (LGPD).
3. **Escopo de expansao:** O modelo de seguranca urbana pode ser replicado para outros bairros? Isso definiria se a arquitetura atual precisa de parametrizacao adicional.

---

*Fala, Gavea! -- INF2921/CIS2114 2026.1 | Equipe: Andrey, Mauro, Julia, Herbert, Natali*
