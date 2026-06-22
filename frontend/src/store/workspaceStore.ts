import { create } from 'zustand'
import type { WorkspaceFilters, ReportFilters, UserRole } from '@/lib/types'

export type ViewId = 'map' | 'table' | 'keywords' | 'similars' | 'chat' | 'cesta'

const FILTER_KEYS: (keyof WorkspaceFilters)[] = [
  'urgency', 'status', 'type_id', 'author_id', 'since', 'until', 'bbox', 'semanticQuery',
]

interface WorkspaceState {
  // committed filters — what views query against
  filters: WorkspaceFilters
  // draft filters — what the panel edits before Apply
  draftFilters: WorkspaceFilters
  selectedIds: Set<string>
  activeViews: ViewId[]
  similarSeedId: string | null
  panelOpen: boolean
  loadedPresetName: string | null
  loadedPresetId: string | null
  draftFilterName: string
  nlSuggestion: Partial<WorkspaceFilters> | null
  nlWarnings: string[]

  // actions
  setFilter: (patch: Partial<WorkspaceFilters>) => void
  setDraftFilter: (patch: Partial<WorkspaceFilters>) => void
  applyFilters: () => void
  clearFilters: () => void
  discardDraft: () => void
  removeFilter: (key: keyof WorkspaceFilters) => void
  setBbox: (bbox: string | undefined) => void
  setSemanticQuery: (q: string) => void
  toggleSelect: (id: string) => void
  clearSelection: () => void
  toggleView: (id: ViewId) => void
  showView: (id: ViewId) => void
  setSimilarSeed: (id: string | null) => void
  togglePanel: () => void
  setLoadedPresetName: (name: string | null) => void
  setLoadedPresetId: (id: string | null) => void
  setDraftFilterName: (name: string) => void
  setNLSuggestion: (suggestion: Partial<WorkspaceFilters> | null, warnings: string[]) => void
  applyNLSuggestion: (suggestion: Partial<WorkspaceFilters>) => void

  // derived selectors (functions — not stored state)
  structuredFilters: () => ReportFilters
  isDirty: () => boolean
}

export function defaultViewsForRole(role: UserRole | undefined): ViewId[] {
  if (role === 'agent' || role === 'admin') return ['map', 'table', 'cesta', 'keywords', 'similars', 'chat']
  return ['map', 'table']
}

export const useWorkspaceStore = create<WorkspaceState>()((set, get) => ({
  filters: {},
  draftFilters: {},
  selectedIds: new Set<string>(),
  activeViews: ['map', 'table'],
  similarSeedId: null,
  panelOpen: true,
  loadedPresetName: null,
  loadedPresetId: null,
  draftFilterName: '',
  nlSuggestion: null,
  nlWarnings: [],

  // Alias for backward compat — routes to draftFilters
  setFilter: (patch: Partial<WorkspaceFilters>) =>
    set((state) => ({ draftFilters: { ...state.draftFilters, ...patch } })),

  setDraftFilter: (patch: Partial<WorkspaceFilters>) =>
    set((state) => ({ draftFilters: { ...state.draftFilters, ...patch } })),

  applyFilters: () =>
    set((state) => ({ filters: { ...state.draftFilters } })),

  clearFilters: () =>
    set({ filters: {}, draftFilters: {}, loadedPresetName: null, loadedPresetId: null, draftFilterName: '' }),

  discardDraft: () =>
    set((state) => ({ draftFilters: { ...state.filters }, loadedPresetName: null })),

  removeFilter: (key: keyof WorkspaceFilters) =>
    set((state) => {
      const nextFilters = { ...state.filters }
      const nextDraft = { ...state.draftFilters }
      delete nextFilters[key]
      delete nextDraft[key]
      return { filters: nextFilters, draftFilters: nextDraft }
    }),

  // setBbox commits to BOTH slices immediately
  setBbox: (bbox: string | undefined) =>
    set((state) => ({
      filters: { ...state.filters, bbox },
      draftFilters: { ...state.draftFilters, bbox },
    })),

  // setSemanticQuery writes to draft only
  setSemanticQuery: (q: string) =>
    set((state) => ({ draftFilters: { ...state.draftFilters, semanticQuery: q } })),

  toggleSelect: (id: string) =>
    set((state) => {
      const next = new Set(state.selectedIds)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return { selectedIds: next }
    }),

  clearSelection: () => set({ selectedIds: new Set<string>() }),

  toggleView: (id: ViewId) =>
    set((state) => {
      const next = state.activeViews.includes(id)
        ? state.activeViews.filter((v) => v !== id)
        : [...state.activeViews, id]
      return { activeViews: next }
    }),

  showView: (id: ViewId) =>
    set((state) =>
      state.activeViews.includes(id)
        ? state
        : { activeViews: [...state.activeViews, id] },
    ),

  setSimilarSeed: (id: string | null) => set({ similarSeedId: id }),

  togglePanel: () => set((state) => ({ panelOpen: !state.panelOpen })),

  setLoadedPresetName: (name: string | null) =>
    set({ loadedPresetName: name, ...(name === null ? { loadedPresetId: null } : {}) }),

  setLoadedPresetId: (id: string | null) => set({ loadedPresetId: id }),

  setDraftFilterName: (name: string) => set({ draftFilterName: name }),

  setNLSuggestion: (suggestion: Partial<WorkspaceFilters> | null, warnings: string[]) =>
    set({ nlSuggestion: suggestion, nlWarnings: warnings }),

  applyNLSuggestion: (suggestion: Partial<WorkspaceFilters>) =>
    set((state) => ({ draftFilters: { ...state.draftFilters, ...suggestion } })),

  structuredFilters: (): ReportFilters => {
    const { semanticQuery: _sq, ...rest } = get().filters
    return rest
  },

  isDirty: (): boolean => {
    const { filters, draftFilters } = get()
    return FILTER_KEYS.some((k) => filters[k] !== draftFilters[k])
  },
}))
