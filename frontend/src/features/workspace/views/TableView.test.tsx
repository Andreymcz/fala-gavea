import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { TableView } from './TableView'
import type { ReportFeature } from '@/lib/types'

const mockToggle = vi.fn()
const mockSetSimilarSeed = vi.fn()

function makeFeature(overrides: Partial<ReportFeature['properties']> = {}, idx = 0): ReportFeature {
  return {
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [-43.188, -22.972] },
    properties: {
      id: `report-${idx}`,
      text: `Relato número ${idx} com texto bem longo para testar truncamento adequado no componente de tabela`,
      report_type_id: 'type-1',
      urgency: 'alta',
      status: 'pendente',
      created_at: `2026-06-0${(idx % 9) + 1}T10:00:00Z`,
      author_id: 'user-1',
      photo_url: null,
      score: null,
      ...overrides,
    },
  }
}

// 60 items for pagination tests
const sixtyFeatures = Array.from({ length: 60 }, (_, i) => makeFeature({}, i))

const mockUseFilteredReports = vi.fn()

vi.mock('@/hooks/useFilteredReports', () => ({
  useFilteredReports: (...args: unknown[]) => mockUseFilteredReports(...args),
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
      setSimilarSeed: mockSetSimilarSeed,
      structuredFilters: vi.fn(),
    }),
}))

vi.mock('@/hooks/useReportTypes', () => ({
  useReportTypes: () => ({ data: [{ id: 'type-1', name: 'Iluminação' }] }),
}))

afterEach(() => {
  mockToggle.mockClear()
  mockSetSimilarSeed.mockClear()
  mockUseFilteredReports.mockClear()
})

describe('TableView — basic render', () => {
  it('renders without crashing and shows report text truncated', () => {
    mockUseFilteredReports.mockReturnValue({
      features: [makeFeature({ text: 'Buraco na calçada da rua principal' })],
      total: 1,
      count: 1,
      isLoading: false,
      semanticActive: false,
      ranked_by: null,
    })
    render(<TableView />)
    expect(screen.getByText(/Buraco na calçada/)).toBeTruthy()
  })

  it('shows type name from typeMap', () => {
    mockUseFilteredReports.mockReturnValue({
      features: [makeFeature()],
      total: 1,
      count: 1,
      isLoading: false,
      semanticActive: false,
      ranked_by: null,
    })
    render(<TableView />)
    expect(screen.getByText('Iluminação')).toBeTruthy()
  })
})

describe('TableView — column sort', () => {
  it('clicking "Data" header sorts by created_at', () => {
    const features = [
      makeFeature({ created_at: '2026-06-10T10:00:00Z', text: 'Relato B' }, 0),
      makeFeature({ created_at: '2026-06-01T10:00:00Z', text: 'Relato A' }, 1),
    ]
    mockUseFilteredReports.mockReturnValue({
      features,
      total: 2,
      count: 2,
      isLoading: false,
      semanticActive: false,
      ranked_by: null,
    })
    render(<TableView />)
    // Find and click "Data" sort button
    const dataBtn = screen.getByRole('button', { name: /ordenar por data/i })
    fireEvent.click(dataBtn)
    // After click, th should have aria-sort
    const th = dataBtn.closest('th')!
    expect(th.getAttribute('aria-sort')).toBeTruthy()
  })
})

describe('TableView — full-text dialog', () => {
  it('"Ler relato" button opens dialog with full text', async () => {
    const longText = 'Texto completo do relato que deve aparecer no dialog sem truncamento algum de forma alguma mesmo que longo'
    mockUseFilteredReports.mockReturnValue({
      features: [makeFeature({ text: longText })],
      total: 1,
      count: 1,
      isLoading: false,
      semanticActive: false,
      ranked_by: null,
    })
    render(<TableView />)
    const lerBtn = screen.getByRole('button', { name: /ler relato/i })
    fireEvent.click(lerBtn)
    await waitFor(() => {
      expect(screen.getByText(longText)).toBeTruthy()
    })
  })
})

describe('TableView — pagination', () => {
  it('page 2 accessible via Próxima button', () => {
    mockUseFilteredReports.mockReturnValue({
      features: sixtyFeatures.slice(0, 50),
      total: 60,
      count: 60,
      isLoading: false,
      semanticActive: false,
      ranked_by: null,
    })
    render(<TableView />)
    expect(screen.getByText(/60 relatos encontrados/)).toBeTruthy()
    const nextBtn = screen.getByRole('button', { name: /próxima/i })
    expect(nextBtn).toBeTruthy()
    fireEvent.click(nextBtn)
    // After going to page 2, the controls row updates to "página 2 de 2"
    const controlSpan = document.querySelector('span.text-xs.text-gray-500')
    expect(controlSpan?.textContent).toMatch(/página 2/i)
  })

  it('Anterior button disabled on first page', () => {
    mockUseFilteredReports.mockReturnValue({
      features: sixtyFeatures.slice(0, 50),
      total: 60,
      count: 60,
      isLoading: false,
      semanticActive: false,
      ranked_by: null,
    })
    render(<TableView />)
    const prevBtn = screen.getByRole('button', { name: /anterior/i })
    expect(prevBtn.hasAttribute('disabled')).toBe(true)
  })
})

describe('TableView — score column', () => {
  it('score column renders only when ranked_by is similarity', () => {
    mockUseFilteredReports.mockReturnValue({
      features: [makeFeature({ score: 0.8 })],
      total: 1,
      count: 1,
      isLoading: false,
      semanticActive: true,
      ranked_by: 'similarity',
    })
    render(<TableView />)
    expect(screen.getByRole('button', { name: /ordenar por relevância/i })).toBeTruthy()
  })

  it('score column not visible when ranked_by is not similarity', () => {
    mockUseFilteredReports.mockReturnValue({
      features: [makeFeature({ score: null })],
      total: 1,
      count: 1,
      isLoading: false,
      semanticActive: false,
      ranked_by: null,
    })
    render(<TableView />)
    expect(screen.queryByText('Relevância')).toBeNull()
  })

  it('score cell with value 0.8 shows sr-only text "(alta)"', () => {
    mockUseFilteredReports.mockReturnValue({
      features: [makeFeature({ score: 0.8 })],
      total: 1,
      count: 1,
      isLoading: false,
      semanticActive: true,
      ranked_by: 'similarity',
    })
    render(<TableView />)
    const srOnly = screen.getByText('(alta)')
    expect(srOnly.classList.contains('sr-only')).toBe(true)
  })
})
