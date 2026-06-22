import { render, fireEvent, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const setDraftFilter = vi.fn()
let mockDraftFilters: Record<string, unknown> = {}

vi.mock('@/store/workspaceStore', () => ({
  useWorkspaceStore: (sel: (s: Record<string, unknown>) => unknown) =>
    sel({
      draftFilters: mockDraftFilters,
      filters: {},
      draftFilterName: '',
      setDraftFilter,
      setFilter: setDraftFilter,
      applyFilters: vi.fn(),
      clearFilters: vi.fn(),
      setSemanticQuery: vi.fn(),
      togglePanel: vi.fn(),
      panelOpen: true,
      loadedPresetName: null,
      loadedPresetId: null,
      setLoadedPresetName: vi.fn(),
      setLoadedPresetId: vi.fn(),
      setDraftFilterName: vi.fn(),
      isDirty: () => false,
      nlSuggestion: null,
      nlWarnings: [],
      setNLSuggestion: vi.fn(),
      applyNLSuggestion: vi.fn(),
    }),
}))

vi.mock('@/hooks/useReportTypes', () => ({ useReportTypes: () => ({ data: [] }) }))
vi.mock('@/hooks/useFilteredReports', () => ({
  useFilteredReports: () => ({ count: 0, semanticTruncated: false, features: [], isLoading: false, semanticActive: false }),
}))
vi.mock('@tanstack/react-query', () => ({
  useQuery: () => ({ data: [], isError: false }),
  useMutation: () => ({ mutate: vi.fn(), isPending: false }),
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
}))
vi.mock('@/lib/api', () => ({ api: {} }))

let mockUser: { id: string } | null = { id: 'user-42' }
vi.mock('@/auth/useAuth', () => ({
  useAuth: () => ({ token: 'tok', user: mockUser, isLoading: false }),
}))
vi.mock('@/api/nlFilter', () => ({ postNLFilter: vi.fn() }))

import { FilterPanel } from './FilterPanel'

beforeEach(() => {
  vi.clearAllMocks()
  mockDraftFilters = {}
  mockUser = { id: 'user-42' }
})

describe('FilterPanel — Meus relatos toggle', () => {
  it('toggle is visible for a logged-in user', () => {
    render(<FilterPanel />)
    expect(screen.getByText(/meus relatos/i)).toBeTruthy()
  })

  it('checking the toggle sets author_id to the current user id', () => {
    render(<FilterPanel />)
    const checkbox = screen.getByRole('checkbox', { name: /meus relatos/i })
    fireEvent.click(checkbox)
    expect(setDraftFilter).toHaveBeenCalledWith({ author_id: 'user-42' })
  })

  it('unchecking the toggle clears author_id', () => {
    mockDraftFilters = { author_id: 'user-42' }
    render(<FilterPanel />)
    const checkbox = screen.getByRole('checkbox', { name: /meus relatos/i }) as HTMLInputElement
    expect(checkbox.checked).toBe(true)
    fireEvent.click(checkbox)
    expect(setDraftFilter).toHaveBeenCalledWith({ author_id: undefined })
  })

  it('toggle is hidden for anonymous users', () => {
    mockUser = null
    render(<FilterPanel />)
    expect(screen.queryByText(/meus relatos/i)).toBeNull()
  })
})
