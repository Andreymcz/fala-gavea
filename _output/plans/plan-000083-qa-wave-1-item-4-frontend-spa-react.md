# Plan 000083 | QA | 2026-06-18 14:19 UTC | qa-wave-1-item-4-frontend-spa-react

source: plan-000082 -- QA companion for frontend SPA planning session

## Brief

roadmap 71 item 4: frontend com tecnologias modernas (fugir de paginas estaticas, visual mais fluido e moderno)

## Q&A Log

**Q: Qual stack de frontend adotar para o Item 4 (substituindo o HTML estatico + Leaflet + Alpine.js da D-006)?**

A: React + Vite + TS -- SPA com React 18, Vite, TypeScript, react-leaflet, TanStack Query, React Router. Build gera assets estaticos servidos pelo FastAPI StaticFiles.

**Q: Qual abordagem de estilo/UI para o 'visual mais moderno'?**

A: Tailwind + shadcn-style -- Tailwind CSS + componentes headless no estilo shadcn/ui (Radix). Mantem a paleta da design-standards.md como theme tokens.

**Q: Qual o escopo deste plano para o Item 4?**

A: SPA completo (4 telas) -- Mapa publico + form de relato (cidadao) + painel do agente + login, cobrindo JM-TB-001 e JM-TB-002.

## Key Decisions Recorded

- Stack selected supersedes D-006 (HTML estatico + Alpine.js). New decision D-007 to be written in Step 11 of plan-000082 via apply_marker.py.
- No CORS: Vite proxy in dev, same-origin StaticFiles in prod. Aligns with S1/C1.
- GET /auth/me added to backend (Step 1) because JWT carries only sub; SPA needs role for conditional UI.
- login endpoint uses application/x-www-form-urlencoded (OAuth2PasswordRequestForm) -- captured in api.ts spec.
- Wave-2 search/chat ships as disabled stubs (layout present, no behavior).
