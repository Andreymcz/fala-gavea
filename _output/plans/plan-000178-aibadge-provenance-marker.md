# Plan 000178 | FEATURE-X | 2026-06-26 12:22 | Reusable AiBadge AI-provenance marker | Review: standard
plan_format_version: 1
source: research-000176 -- IA markers on AI features + forwarding comment synthesis (Decision D-015)
revised: 2026-06-26 -- added platform-helper "Ajuda" chat (HelpChat, plan-000177/D-014/D-017) as a 4th marker site; it was implemented after this plan was first written

## Brief

source: research-000176 Deliverable A only: reusable AiBadge AI-provenance marker component. Build frontend/src/components/AiBadge.tsx (✨ sparkles icon + short visible "IA" text + tooltip "Conteúdo gerado por IA — pode conter erros. Revise antes de agir."), with mandatory accessible name (aria-label). Apply consistently at the confirmed AI surfaces: NL chat tab (ViewToggleBar), NL filter + semantic search assistant (FilterPanel), and reserve usage for report-type suggestion when plan-000174 lands. Exclude auto-keyword feature. No backend, no i18n framework (hardcode pt-BR). Decision recorded as D-015. Frontend-only; include component test (vitest).

## Agent Interpretation

Create one reusable React component `AiBadge` that visually signals "this content/feature is AI-generated" and apply it consistently at the AI touchpoints, replacing today's ad-hoc `(IA)` text labels. Per D-015 the visual is the sparkles icon ✨ plus a short visible "IA" text plus a tooltip; the visible "IA" text doubles as the accessible name (resolving the A11y gap the research flagged for an icon-only marker). Frontend-only — no API, schema, or i18n-framework changes; copy is hardcoded pt-BR per project convention.

Scope of application (research-000176 confirmed sites + one new surface implemented since):
- **Chat tab** in `ViewToggleBar.tsx` — replace the inline `(IA)` text in the chat view description with the badge.
- **NL filter + semantic search** assistant in `FilterPanel.tsx` — badge next to the "Assistente de filtros" label (this assistant drives both the NL filter and semantic search).
- **Platform-helper "Ajuda" chat** (`HelpChat`, mounted in `Header.tsx`) — *new surface, implemented after research-000176 by plan-000177 (D-014) and refined by plan-000181 (D-017)*. This RAG-over-docs assistant is available to all authenticated users and currently carries no AI-provenance marker. Add the badge next to the "Ajuda da plataforma" dialog title.
- **Report-type suggestion** — still out of scope to wire here (feature unbuilt, plan-000174 not yet implemented as of this revision); the component is designed so plan-000174 can drop it in. Documented, not implemented.
- **Excluded**: auto-keyword view (`keywords`) — user excluded it from marker scope.

`lucide-react` is the icon source if already a dependency; otherwise use an inline SVG sparkles glyph (Step 1 verifies which).

## Files

### Created
- `frontend/src/components/AiBadge.tsx` -- reusable AI-provenance badge (icon + "IA" text + tooltip)
- `frontend/src/components/AiBadge.test.tsx` -- vitest: accessible name + tooltip text present

### Modified
- `frontend/src/features/workspace/ViewToggleBar.tsx` -- chat view marker via AiBadge (remove inline "(IA)")
- `frontend/src/features/workspace/FilterPanel.tsx` -- AiBadge next to "Assistente de filtros" label
- `frontend/src/components/layout/Header.tsx` -- AiBadge next to the "Ajuda da plataforma" dialog title (platform-helper chat)

---

## Steps

### Step 1: Build the reusable AiBadge component

Create `frontend/src/components/AiBadge.tsx`. Requirements:
- Renders a sparkles icon + the short visible text `IA`, styled as a small inline pill consistent with the existing `Badge` (`components/ui/badge.tsx`) tokens (rounded-full, `text-xs`/`text-[10px]`, muted bg). Do **not** add a variant to `badge.tsx`; `AiBadge` is a standalone wrapper so AI semantics live in one place.
- **Icon**: check `frontend/package.json` for `lucide-react`. If present, use `<Sparkles aria-hidden="true" className="h-3 w-3" />`. If absent, inline a small SVG sparkles glyph with `aria-hidden="true"`. Do not add a new dependency for this.
- **Accessible name**: the visible "IA" text provides it; additionally set `aria-label="Conteúdo gerado por IA"` on the wrapper so screen readers get the full meaning, and `title`/tooltip = `"Conteúdo gerado por IA — pode conter erros. Revise antes de agir."`. Use the native `title` attribute for the tooltip (no tooltip library dependency; keyboard/touch reachable as plain text) unless a shadcn `Tooltip` primitive already exists under `components/ui/` (Step verifies; if it exists, use it with the trigger focusable).
- Accept optional props: `className?: string` (layout overrides) and `size?: 'sm' | 'xs'` (default `xs`) so it fits both the toggle-bar description line and the filter label.
- Pure presentational component; no state, no data fetching.

- **Files**: `frontend/src/components/AiBadge.tsx` (create)
- **References**: `frontend/src/components/ui/badge.tsx` (token reference), product-design D-015
- **Interface**: `export function AiBadge(props: { className?: string; size?: 'sm' | 'xs' }): JSX.Element`
- **Depends on**: none
- **Verify**: `cd frontend && npx tsc --noEmit` exits 0
- **Tests**: covered in Step 2
- **Docs**: N/A
- [ ] Done

### Step 2: Component test for AiBadge

Create `frontend/src/components/AiBadge.test.tsx` (vitest + @testing-library/react, matching existing test style e.g. `ViewToggleBar.test.tsx`):
1. Renders an element whose accessible name is "Conteúdo gerado por IA" (`getByLabelText` or `getByRole` with name) — locks in the A11y floor from D-015.
2. The visible "IA" text is present.
3. The tooltip text "Conteúdo gerado por IA — pode conter erros. Revise antes de agir." is present (via `title` attribute or tooltip content).
4. The decorative icon is `aria-hidden` (not part of the accessible name).

- **Files**: `frontend/src/components/AiBadge.test.tsx` (create)
- **Depends on**: Step 1
- **Verify**: `cd frontend && npx vitest run src/components/AiBadge.test.tsx` passes
- **Tests**: this step is the test
- **Docs**: N/A
- [ ] Done

### Step 3: Apply AiBadge to the Chat view marker (ViewToggleBar)

In `frontend/src/features/workspace/ViewToggleBar.tsx`:
- Remove the inline `(IA)` text from the chat entry description (`ViewToggleBar.tsx:18`): change `'Pergunte sobre os relatos em linguagem natural (IA)'` to `'Pergunte sobre os relatos em linguagem natural'`.
- Add an optional `ai?: boolean` field to `ViewMeta`; set `ai: true` on the chat entry.
- In the button render, when `meta.ai`, render `<AiBadge size="xs" />` inline at the end of the label row (next to `meta.label`). Keep the existing `aria-label={`${meta.label}: ${meta.description}`}` on the button; the badge's own `aria-label` adds the AI provenance. Ensure the badge does not break the existing flex layout (it sits in the label `<span>` row).

- **Files**: `frontend/src/features/workspace/ViewToggleBar.tsx` (modify)
- **References**: existing `VIEW_META` structure
- **Depends on**: Step 1
- **Interface**: `ViewMeta` gains `ai?: boolean`
- **Verify**: `cd frontend && npm run build` exits 0; chat toggle shows the ✨ IA badge and no longer shows literal "(IA)"
- **Tests**: extend `ViewToggleBar.test.tsx` — assert the chat button contains an element with accessible name "Conteúdo gerado por IA"; assert the literal "(IA)" is gone
- **Docs**: N/A
- [ ] Done

### Step 4: Apply AiBadge to the NL filter / semantic search assistant (FilterPanel)

In `frontend/src/features/workspace/FilterPanel.tsx`, Section 4 ("NL assistant footer", around line 467):
- Change the label row from a bare `<p>Assistente de filtros</p>` to a flex row containing the text and `<AiBadge size="xs" />`: e.g. `<div className="flex items-center gap-1.5"><p className="text-xs text-gray-500 font-medium">Assistente de filtros</p><AiBadge size="xs" /></div>`.
- This assistant powers both the NL filter parse and semantic search, so one badge here covers both surfaces (per research scope). Do not add a second badge to the semantic-search input.

- **Files**: `frontend/src/features/workspace/FilterPanel.tsx` (modify)
- **Depends on**: Step 1
- **Interface**: N/A (UI only)
- **Verify**: `cd frontend && npm run build` exits 0; the "Assistente de filtros" label shows the ✨ IA badge
- **Tests**: `cd frontend && npm run test` passes; existing `FilterPanel.test.tsx` still green (badge addition is non-breaking — assert presence of accessible name "Conteúdo gerado por IA" within the assistant section if a test already renders it)
- **Docs**: N/A
- [ ] Done

### Step 5: Apply AiBadge to the platform-helper "Ajuda" chat (Header dialog)

The platform-helper chat (`HelpChat`) was implemented after research-000176 (plan-000177/D-014, refined by plan-000181/D-017). It is a RAG-over-docs assistant in a dialog and currently has no AI-provenance marker. It is mounted in `frontend/src/components/layout/Header.tsx` inside a `Dialog` whose `DialogTitle` is "Ajuda da plataforma" (around line 127).

- In `Header.tsx`, render `<AiBadge size="xs" />` next to the `DialogTitle` "Ajuda da plataforma" — e.g. wrap the title text and badge in a flex row inside `<DialogTitle>`, or place the badge immediately after it. Keep the existing `DialogDescription` ("Assistente sobre como usar o Fala-Gávea...") unchanged.
- Do NOT add a second badge inside `HelpChat.tsx` itself — one marker at the dialog title is sufficient and avoids duplication. (The intro line in `HelpChat.tsx` already says "As respostas vêm da documentação do sistema"; leave it.)
- Verify the badge does not disrupt the `DialogHeader` layout (it is a small inline pill).

- **Files**: `frontend/src/components/layout/Header.tsx` (modify)
- **References**: `frontend/src/features/help/HelpChat.tsx` (the surface being marked), `frontend/src/components/AiBadge.tsx` (Step 1)
- **Depends on**: Step 1
- **Interface**: N/A (UI only)
- **Verify**: `cd frontend && npm run build` exits 0; opening the "Ajuda da plataforma" dialog shows the ✨ IA badge next to the title
- **Tests**: `cd frontend && npm run test` passes; `HelpChat.test.tsx` still green. If a test renders the help dialog (Header), assert the badge's accessible name "Conteúdo gerado por IA" is present; otherwise a visual check suffices (badge lives in Header, not HelpChat).
- **Docs**: N/A
- [ ] Done

---

## Review

### Engineering perspectives

| Perspective | Status | Notes |
|---|---|---|
| P0 - Correctness | Adopted | Pure presentational component; no logic to get wrong. Removing the literal "(IA)" is the only behavioral change, covered by a test assertion. |
| P0 - Security | N/A | Frontend display-only; no data, no auth, no user input. |
| P1 - Architecture | Adopted | Single source of AI-provenance semantics (`AiBadge`); wraps existing Badge tokens without polluting `badge.tsx` variants. |
| P1 - Accessibility | Adopted | D-015 floor enforced: visible "IA" text + `aria-label="Conteúdo gerado por IA"`; decorative icon `aria-hidden`; tooltip is plain `title`/focusable text (not hover-only) — directly addresses the research A11y finding. |
| P2 - Consistency (metacomm) | Adopted | Replaces ad-hoc per-feature "(IA)" labels with one consistent signal across chat + filter + platform-helper "Ajuda" chat; report-type suggestion slot reserved for plan-000174. Now covers all 3 live AI surfaces (the help chat was added after research-000176). |
| P2 - Testing | Adopted | Dedicated component test for the accessible name + tooltip; toggle-bar test asserts marker presence and literal removal. |
| P3 - Dependencies | Adopted | No new dependency: reuse `lucide-react` if already present, else inline SVG. Step 1 verifies. |
| P4 - i18n | Adopted | No i18n framework in project; hardcode pt-BR per convention. |

### Trade-offs
- **Standalone AiBadge vs new `badge.tsx` variant**: a standalone wrapper keeps AI semantics (icon + aria-label + tooltip) in one file; a `badge.tsx` variant would only give styling and force each call site to re-add the icon/aria-label. Standalone wins for consistency.
- **Native `title` tooltip vs tooltip library**: `title` is zero-dependency and keyboard/touch reachable as plain text, satisfying the A11y concern without adding a Radix tooltip. If a shadcn `Tooltip` primitive already exists it can be used instead; otherwise not worth a new dependency for two call sites.
- **Icon-only (user's first instinct) vs icon+text**: D-015 settled on icon + short "IA" text precisely because icon-only fails the accessible-name and metacommunication (IIc1 "What's this?") checks. This plan implements the resolved decision.

---

## Test Plan

1. `cd frontend && npx vitest run src/components/AiBadge.test.tsx` — passes (accessible name, visible text, tooltip, aria-hidden icon).
2. `cd frontend && npm run test` — full frontend suite green (note: pre-existing unrelated failure in `PublicForwardingsPage.test.tsx` due to missing AuthProvider wrapper is out of scope).
3. `cd frontend && npm run build` — exits 0.
4. Visual: open workspace as agent → Chat toggle shows ✨ IA badge, no literal "(IA)"; hovering/focusing shows the tooltip.
5. Visual: FilterPanel "Assistente de filtros" label shows the ✨ IA badge.
6. Visual: open the "Ajuda da plataforma" dialog (any authenticated user) → ✨ IA badge appears next to the title.
7. Screen-reader smoke (optional): the badge announces "Conteúdo gerado por IA" at all three sites.

## Notes / Follow-ups
- When plan-000174 (report-type suggestion) is implemented, drop `<AiBadge />` on the AI-suggested type chip/row instead of inventing a new `<Badge variant="outline">IA</Badge>` (that plan's Step 9 currently proposes an ad-hoc badge — supersede it with `AiBadge`).
