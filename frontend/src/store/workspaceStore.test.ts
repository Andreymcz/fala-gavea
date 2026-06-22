import { describe, it, expect, afterEach } from 'vitest'
import { useWorkspaceStore, defaultViewsForRole } from './workspaceStore'

const resetStore = () =>
  useWorkspaceStore.setState({
    filters: {},
    draftFilters: {},
    selectedIds: new Set(),
    activeViews: ['map', 'table'],
    similarSeedId: null,
    panelOpen: true,
    loadedPresetName: null,
    draftFilterName: '',
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

  it('setBbox updates filters.bbox AND draftFilters.bbox', () => {
    const store = useWorkspaceStore.getState()
    store.setBbox('-43.2,-22.9,-43.1,-22.8')
    const state = useWorkspaceStore.getState()
    expect(state.filters.bbox).toBe('-43.2,-22.9,-43.1,-22.8')
    expect(state.draftFilters.bbox).toBe('-43.2,-22.9,-43.1,-22.8')
  })

  it('setBbox: isDirty() is false after setBbox (both slices updated)', () => {
    const store = useWorkspaceStore.getState()
    store.setBbox('-43.2,-22.9,-43.1,-22.8')
    expect(useWorkspaceStore.getState().isDirty()).toBe(false)
  })

  it('structuredFilters excludes semanticQuery', () => {
    const store = useWorkspaceStore.getState()
    store.setFilter({ urgency: 'alta', semanticQuery: 'buraco na rua' })
    // apply draft so structuredFilters reads committed
    useWorkspaceStore.getState().applyFilters()
    const sf = useWorkspaceStore.getState().structuredFilters()
    expect(sf).toEqual({ urgency: 'alta' })
    expect('semanticQuery' in sf).toBe(false)
  })

  // --- new draft/commit split tests ---

  it('setDraftFilter changes draftFilters, not committed filters', () => {
    const store = useWorkspaceStore.getState()
    store.setDraftFilter({ urgency: 'alta' })
    const state = useWorkspaceStore.getState()
    expect(state.draftFilters.urgency).toBe('alta')
    expect(state.filters.urgency).toBeUndefined()
  })

  it('applyFilters copies draft to committed; isDirty() is false after apply', () => {
    const store = useWorkspaceStore.getState()
    store.setDraftFilter({ urgency: 'media' })
    expect(useWorkspaceStore.getState().isDirty()).toBe(true)
    useWorkspaceStore.getState().applyFilters()
    const state = useWorkspaceStore.getState()
    expect(state.filters.urgency).toBe('media')
    expect(state.isDirty()).toBe(false)
  })

  it('isDirty() is true after setDraftFilter, false after clearFilters', () => {
    const store = useWorkspaceStore.getState()
    store.setDraftFilter({ urgency: 'baixa' })
    expect(useWorkspaceStore.getState().isDirty()).toBe(true)
    useWorkspaceStore.getState().clearFilters()
    expect(useWorkspaceStore.getState().isDirty()).toBe(false)
  })

  it('removeFilter drops key from both filters and draftFilters', () => {
    useWorkspaceStore.setState({ filters: { urgency: 'alta' }, draftFilters: { urgency: 'alta' } })
    useWorkspaceStore.getState().removeFilter('urgency')
    const state = useWorkspaceStore.getState()
    expect(state.filters.urgency).toBeUndefined()
    expect(state.draftFilters.urgency).toBeUndefined()
  })

  it('discardDraft resets draftFilters to match committed filters', () => {
    useWorkspaceStore.setState({ filters: { urgency: 'alta' }, draftFilters: { urgency: 'media' }, loadedPresetName: 'preset-x' })
    useWorkspaceStore.getState().discardDraft()
    const state = useWorkspaceStore.getState()
    expect(state.draftFilters).toEqual({ urgency: 'alta' })
    expect(state.loadedPresetName).toBeNull()
  })

  it('clearFilters resets all name fields to defaults', () => {
    useWorkspaceStore.setState({ loadedPresetName: 'foo', draftFilterName: 'bar' })
    useWorkspaceStore.getState().clearFilters()
    const state = useWorkspaceStore.getState()
    expect(state.loadedPresetName).toBeNull()
    expect(state.draftFilterName).toBe('')
    expect(state.filters).toEqual({})
    expect(state.draftFilters).toEqual({})
  })

  it('setSemanticQuery writes to draft only', () => {
    useWorkspaceStore.getState().setSemanticQuery('enchente')
    const state = useWorkspaceStore.getState()
    expect(state.draftFilters.semanticQuery).toBe('enchente')
    expect(state.filters.semanticQuery).toBeUndefined()
  })

  it('togglePanel flips panelOpen', () => {
    expect(useWorkspaceStore.getState().panelOpen).toBe(true)
    useWorkspaceStore.getState().togglePanel()
    expect(useWorkspaceStore.getState().panelOpen).toBe(false)
  })

  it("defaultViewsForRole includes 'cesta' for agent/admin, not for citizen", () => {
    expect(defaultViewsForRole('agent')).toContain('cesta')
    expect(defaultViewsForRole('admin')).toContain('cesta')
    expect(defaultViewsForRole('citizen')).not.toContain('cesta')
    expect(defaultViewsForRole(undefined)).not.toContain('cesta')
  })

  it("showView adds 'cesta' when absent and is idempotent", () => {
    useWorkspaceStore.setState({ activeViews: ['map', 'table'] })
    useWorkspaceStore.getState().showView('cesta')
    expect(useWorkspaceStore.getState().activeViews).toContain('cesta')
    const len = useWorkspaceStore.getState().activeViews.length
    // calling again does not duplicate
    useWorkspaceStore.getState().showView('cesta')
    expect(useWorkspaceStore.getState().activeViews.length).toBe(len)
  })

  it('setLoadedPresetName and setDraftFilterName work', () => {
    useWorkspaceStore.getState().setLoadedPresetName('my-preset')
    useWorkspaceStore.getState().setDraftFilterName('new name')
    const state = useWorkspaceStore.getState()
    expect(state.loadedPresetName).toBe('my-preset')
    expect(state.draftFilterName).toBe('new name')
  })
})
