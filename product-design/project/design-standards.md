---
designer_description: "UX and visual-design conventions for fala-gavea — map-centric interface, form patterns, feedback, and accessibility baseline so every screen is reviewed against one agreed baseline."
---

# DESIGN STANDARDS — fala-gavea

---

## UX Patterns

### 1. App Type & Default Pattern Set

**Selected app type:** Map-Centric Civic App (híbrido: Dashboard + CRUD Admin)

O app tem dois modos de uso: cidadão (formulário de registro + mapa público) e agente/admin (mapa interativo + painel de encaminhamentos). A interface primária é o mapa — não uma lista ou sidebar tradicional.

---

### 2. Navigation Patterns

**Primary Navigation:** Mapa como hub central. Links no header para login, formulário de relato, e painel do agente.

| Página | Acesso | Audience |
|--------|--------|----------|
| index.html (mapa) | Público (URL direta) | Todos |
| report.html | Link no mapa (cidadão autenticado) | citizen |
| agent.html | Link no header (agente autenticado) | agent, admin |
| login.html | Link no header se não autenticado | Todos |

**Secondary Navigation:** Filtros na sidebar do mapa (tipo, urgência, status, data). Sem breadcrumbs (app de profundidade 1).

---

### 3. Form Patterns

- **Validação:** On-submit com highlight de campos inválidos. Sem validação inline para manter simplicidade.
- **Geolocalização:** Botão "Usar minha localização" preenche lat/lon automaticamente. Fallback: campos editáveis.
- **Selects:** Tipo de problema e urgência como `<select>` nativos. Sem custom dropdowns no PoC.
- **Feedback:** Toast de confirmação (3s) após submit bem-sucedido. Redirect para mapa mostrando o relato criado.

---

### 4. Map Interaction Patterns

- **Marcadores:** Coloridos por urgência (vermelho=alta, laranja=média, azul=baixa). Popup com tipo, texto, status, data.
- **Busca semântica:** Layer separado com pins roxos. Campo de busca na sidebar.
- **Seleção para encaminhamento:** Checkbox por marcador (visível apenas para agente autenticado). Botão flutuante "Criar encaminhamento" aparece quando ≥1 relato selecionado. Contador no botão.
- **Modal de encaminhamento:** Overlay com campos institution (text) e proposed_solution (textarea). Botão confirmar.

---

### 5. Empty States

| Contexto | Mensagem |
|----------|----------|
| Mapa sem relatos | "Nenhum relato registrado na Gávea ainda. Seja o primeiro!" |
| Busca sem resultados | "Nenhum relato encontrado para esta busca." |
| Painel do agente sem encaminhamentos | "Nenhum encaminhamento criado ainda." |
| Filtros sem resultados | "Nenhum relato corresponde aos filtros selecionados." |

---

### 6. Feedback Patterns

| Ação | Feedback |
|------|---------|
| Relato registrado | Toast verde: "Relato registrado com sucesso!" |
| Encaminhamento criado | Toast verde: "Encaminhamento criado para [institution]." |
| Erro de autenticação | Toast vermelho: "Email ou senha incorretos." |
| Erro de servidor | Toast vermelho: "Erro ao processar sua solicitação. Tente novamente." |
| Geolocalização negada | Alert inline: "Geolocalização não disponível. Preencha latitude e longitude manualmente." |

---

### 7. Accessibility

- HTML semântico: `<form>`, `<label for>`, `<button type>`, `<main>`, `<nav>`, `<header>`.
- Contraste mínimo WCAG AA para texto sobre fundo.
- Marcadores do mapa com `title` para screen readers.
- Todos os inputs com `<label>` ou `aria-label`.

---

## Visual Design

### 1. Typography

Fontes do sistema (sem CDN externo): `font-family: system-ui, -apple-system, sans-serif`.

### 2. Color Palette

| Token | Hex | Uso |
|-------|-----|-----|
| urgency-alta | #E53E3E | Marcadores vermelhos, badge urgência alta |
| urgency-media | #DD6B20 | Marcadores laranjas, badge urgência média |
| urgency-baixa | #3182CE | Marcadores azuis, badge urgência baixa |
| search-result | #805AD5 | Pins roxos para resultados de busca semântica |
| success | #38A169 | Toast de sucesso |
| error | #E53E3E | Toast de erro |
| neutral | #718096 | Texto secundário |
| background | #F7FAFC | Fundo de páginas |

### 3. Component Inventory

| Component | Páginas | Notes |
|-----------|---------|-------|
| Mapa Leaflet | index.html | Centro: Gávea (-22.9731, -43.2272), zoom 15 |
| Sidebar de filtros | index.html | Tipo, urgência, status, data_de, data_ate |
| Botão flutuante | index.html | Visível apenas para agente; mostra contagem selecionados |
| Modal de encaminhamento | index.html | Alpine.js x-show |
| Chat flutuante | index.html | Alpine.js; minimizável |
| Formulário de relato | report.html | — |
| Tabela de encaminhamentos | agent.html | Click expande relatos; dropdown inline de status |
| Toast notification | Todas | Alpine.js; auto-dismiss 3s |
| Login form | login.html | — |
