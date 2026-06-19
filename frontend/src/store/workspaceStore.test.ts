import { describe, it, expect, afterEach } from 'vitest'
import { useWorkspaceStore } from './workspaceStore'

const resetStore = () =>
  useWorkspaceStore.setState({
    filters: {},
    selectedIds: new Set(),
    activeViews: ['map', 'table'],
    similarSeedId: null,
  })

afterEach(() => {
  resetStore()
})

describe('workspaceStore', () => {
  it('toggleSelect is idempotent — toggling same id twice yields empty set', () => {
    const store = useWorkspaceStore.getState()
    store.toggleSelect('abc')
    store.toggleSelect('abc')
    expect(useWorkspaceStore.getState().selectedIds.size).toBe(0)
  })

  it('clearFilters does NOT clear selectedIds', () => {
    const store = useWorkspaceStore.getState()
    store.toggleSelect('xyz')
    store.setFilter({ urgency: 'alta' })
    store.clearFilters()
    const state = useWorkspaceStore.getState()
    expect(state.filters).toEqual({})
    expect(state.selectedIds.has('xyz')).toBe(true)
  })

  it('setBbox updates filters.bbox', () => {
    const store = useWorkspaceStore.getState()
    store.setBbox('-43.2,-22.9,-43.1,-22.8')
    expect(useWorkspaceStore.getState().filters.bbox).toBe('-43.2,-22.9,-43.1,-22.8')
  })

  it('structuredFilters excludes semanticQuery', () => {
    const store = useWorkspaceStore.getState()
    store.setFilter({ urgency: 'alta', semanticQuery: 'buraco na rua' })
    const sf = useWorkspaceStore.getState().structuredFilters()
    expect(sf).toEqual({ urgency: 'alta' })
    expect('semanticQuery' in sf).toBe(false)
  })
})
