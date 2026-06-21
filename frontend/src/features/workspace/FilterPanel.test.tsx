import { render, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const applyFilters = vi.fn()
const clearFilters = vi.fn()
const setDraftFilter = vi.fn()
const setSemanticQuery = vi.fn()
const togglePanel = vi.fn()

let mockIsDirty = false
let mockPanelOpen = true
let mockLoadedPresetName: string | null = null

const getMockStore = (selector: (s: Record<string, unknown>) => unknown) => {
  const store = {
    filters: {},
    draftFilters: { semanticQuery: '' } as Record<string, unknown>,
    setFilter: setDraftFilter,
    setDraftFilter,
    clearFilters,
    setSemanticQuery,
    applyFilters,
    togglePanel,
    panelOpen: mockPanelOpen,
    loadedPresetName: mockLoadedPresetName,
    isDirty: () => mockIsDirty,
  }
  return selector(store as unknown as Record<string, unknown>)
}

vi.mock('@/store/workspaceStore', () => ({
  useWorkspaceStore: (sel: (s: Record<string, unknown>) => unknown) => getMockStore(sel),
}))
vi.mock('@/hooks/useReportTypes', () => ({ useReportTypes: () => ({ data: [] }) }))
vi.mock('@/hooks/useFilteredReports', () => ({
  useFilteredReports: () => ({ count: 5, semanticTruncated: false, features: [], isLoading: false, semanticActive: false }),
}))

import { FilterPanel } from './FilterPanel'

beforeEach(() => {
  vi.clearAllMocks()
  mockIsDirty = false
  mockPanelOpen = true
  mockLoadedPresetName = null
})

describe('FilterPanel', () => {
  it('Aplicar button is disabled when isDirty is false', () => {
    mockIsDirty = false
    const { getByRole } = render(<FilterPanel />)
    const aplicar = getByRole('button', { name: /Aplicar/i })
    expect(aplicar).toBeTruthy()
    expect((aplicar as HTMLButtonElement).disabled).toBe(true)
  })

  it('Aplicar button is enabled when isDirty is true', () => {
    mockIsDirty = true
    const { getByRole } = render(<FilterPanel />)
    const aplicar = getByRole('button', { name: /Aplicar/i })
    expect((aplicar as HTMLButtonElement).disabled).toBe(false)
  })

  it('dirty indicator text renders when isDirty is true', () => {
    mockIsDirty = true
    const { getByText } = render(<FilterPanel />)
    expect(getByText(/Filtros alterados/i)).toBeTruthy()
  })

  it('dirty indicator is absent when isDirty is false', () => {
    mockIsDirty = false
    const { queryByText } = render(<FilterPanel />)
    expect(queryByText(/Filtros alterados/i)).toBeNull()
  })

  it('clicking Aplicar calls applyFilters', () => {
    mockIsDirty = true
    const { getByRole } = render(<FilterPanel />)
    fireEvent.click(getByRole('button', { name: /Aplicar/i }))
    expect(applyFilters).toHaveBeenCalledTimes(1)
  })

  it('clicking Limpar calls clearFilters', () => {
    const { getByRole } = render(<FilterPanel />)
    fireEvent.click(getByRole('button', { name: /Limpar/i }))
    expect(clearFilters).toHaveBeenCalledTimes(1)
  })

  it('Enter in semantic input calls applyFilters', () => {
    const { getByPlaceholderText } = render(<FilterPanel />)
    const input = getByPlaceholderText(/Descreva o que procura/i)
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' })
    expect(applyFilters).toHaveBeenCalledTimes(1)
  })

  it('Section 4 NL placeholder is visible and disabled', () => {
    const { getByPlaceholderText } = render(<FilterPanel />)
    const input = getByPlaceholderText(/Descreva o filtro/i)
    expect(input).toBeTruthy()
    expect((input as HTMLInputElement).disabled).toBe(true)
  })

  it('collapse toggle calls togglePanel', () => {
    const { getByRole } = render(<FilterPanel />)
    const toggle = getByRole('button', { name: /Recolher painel/i })
    fireEvent.click(toggle)
    expect(togglePanel).toHaveBeenCalledTimes(1)
  })

  it('when panelOpen is false, panel collapses and shows expand button', () => {
    mockPanelOpen = false
    const { queryByRole, getByRole } = render(<FilterPanel />)
    // Aplicar button should not be visible in collapsed state
    expect(queryByRole('button', { name: /Aplicar/i })).toBeNull()
    // Expand toggle should be present
    const toggle = getByRole('button', { name: /Expandir painel/i })
    expect(toggle).toBeTruthy()
  })
})
