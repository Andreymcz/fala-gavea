import { create } from 'zustand'
import type { WorkspaceFilters, ReportFilters, UserRole } from '@/lib/types'

export type ViewId = 'map' | 'table' | 'topics' | 'similars' | 'chat'

interface WorkspaceState {
  filters: WorkspaceFilters
  selectedIds: Set<string>
  activeViews: ViewId[]
  similarSeedId: string | null
  // actions
  setFilter: (patch: Partial<WorkspaceFilters>) => void
  clearFilters: () => void
  setBbox: (bbox: string | undefined) => void
  setSemanticQuery: (q: string) => void
  toggleSelect: (id: string) => void
  clearSelection: () => void
  toggleView: (id: ViewId) => void
  setSimilarSeed: (id: string | null) => void
  // derived selector (function — not stored state)
  structuredFilters: () => ReportFilters
}

export function defaultViewsForRole(role: UserRole | undefined): ViewId[] {
  if (role === 'agent' || role === 'admin') return ['map', 'table', 'topics', 'similars', 'chat']
  return ['map', 'table']
}

export const useWorkspaceStore = create<WorkspaceState>()((set, get) => ({
  filters: {},
  selectedIds: new Set<string>(),
  activeViews: ['map', 'table'],
  similarSeedId: null,

  setFilter: (patch: Partial<WorkspaceFilters>) =>
    set((state) => ({ filters: { ...state.filters, ...patch } })),

  clearFilters: () => set({ filters: {} }),

  setBbox: (bbox: string | undefined) =>
    set((state) => ({ filters: { ...state.filters, bbox } })),

  setSemanticQuery: (q: string) =>
    set((state) => ({ filters: { ...state.filters, semanticQuery: q } })),

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

  setSimilarSeed: (id: string | null) => set({ similarSeedId: id }),

  structuredFilters: (): ReportFilters => {
    const { semanticQuery: _sq, ...rest } = get().filters
    return rest
  },
}))
