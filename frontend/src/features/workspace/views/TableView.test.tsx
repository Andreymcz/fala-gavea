import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { TableView } from './TableView'
import type { ReportFeature } from '@/lib/types'

const mockToggle = vi.fn()

const mockFeature: ReportFeature = {
  type: 'Feature',
  geometry: { type: 'Point', coordinates: [-43.188, -22.972] },
  properties: {
    id: 'report-1',
    text: 'Buraco na calçada da rua principal',
    report_type_id: 'type-1',
    urgency: 'alta',
    status: 'pendente',
    created_at: '2026-06-01T10:00:00Z',
    author_id: 'user-1',
    photo_url: null,
  },
}

vi.mock('@/hooks/useFilteredReports', () => ({
  useFilteredReports: () => ({
    features: [mockFeature],
    count: 1,
    isLoading: false,
    semanticActive: false,
    semanticTruncated: false,
  }),
}))

vi.mock('@/store/workspaceStore', () => ({
  useWorkspaceStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({
      selectedIds: new Set<string>(),
      toggleSelect: mockToggle,
      clearSelection: vi.fn(),
      filters: {},
      activeViews: ['map', 'table'],
      similarSeedId: null,
      setFilter: vi.fn(),
      clearFilters: vi.fn(),
      setBbox: vi.fn(),
      setSemanticQuery: vi.fn(),
      toggleView: vi.fn(),
      setSimilarSeed: vi.fn(),
      structuredFilters: vi.fn(),
    }),
}))

vi.mock('@/hooks/useReportTypes', () => ({
  useReportTypes: () => ({ data: [{ id: 'type-1', name: 'Iluminação' }] }),
}))

afterEach(() => {
  mockToggle.mockClear()
})

describe('TableView', () => {
  it('renders without crashing and shows report text', () => {
    render(<TableView />)
    expect(screen.getByText(/Buraco na calçada/)).toBeTruthy()
  })

  it('shows type name from typeMap', () => {
    render(<TableView />)
    expect(screen.getByText('Iluminação')).toBeTruthy()
  })

  it('shows urgency label with shape prefix', () => {
    render(<TableView />)
    expect(screen.getByText('▲ Alta')).toBeTruthy()
  })

  it('calls toggleSelect when row is clicked', () => {
    render(<TableView />)
    const row = screen.getByText(/Buraco na calçada/).closest('tr')!
    fireEvent.click(row)
    expect(mockToggle).toHaveBeenCalledWith('report-1')
  })

  it('calls toggleSelect when checkbox is changed', () => {
    render(<TableView />)
    const checkbox = screen.getByRole('checkbox', { name: /selecionar relato/i })
    fireEvent.click(checkbox)
    expect(mockToggle).toHaveBeenCalledWith('report-1')
  })
})
