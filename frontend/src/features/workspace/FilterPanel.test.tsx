import { render } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

const mockStore = {
  filters: {} as Record<string, unknown>,
  setFilter: vi.fn(),
  clearFilters: vi.fn(),
  setSemanticQuery: vi.fn(),
}

vi.mock('@/store/workspaceStore', () => ({
  useWorkspaceStore: () => mockStore,
}))
vi.mock('@/hooks/useReportTypes', () => ({ useReportTypes: () => ({ data: [] }) }))
vi.mock('@/hooks/useFilteredReports', () => ({
  useFilteredReports: () => ({ count: 5, semanticTruncated: false, features: [], isLoading: false, semanticActive: false }),
}))

import { FilterPanel } from './FilterPanel'

describe('FilterPanel', () => {
  it('renders without crashing', () => {
    const { getByText } = render(<FilterPanel />)
    expect(getByText('Filtros')).toBeTruthy()
  })

  it('shows live count', () => {
    const { getAllByText } = render(<FilterPanel />)
    expect(getAllByText(/5 relatos/).length).toBeGreaterThan(0)
  })
})
