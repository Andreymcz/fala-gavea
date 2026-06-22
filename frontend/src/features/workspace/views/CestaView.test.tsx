import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { CestaView } from './CestaView'
import type { ReportFeature } from '@/lib/types'

const mockToggleSelect = vi.fn()
const mockClearSelection = vi.fn()
let selectedIds = new Set<string>(['report-0', 'report-1'])

function makeFeature(idx: number): ReportFeature {
  return {
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [-43.188, -22.972] },
    properties: {
      id: `report-${idx}`,
      text: `Relato número ${idx}`,
      report_type_id: 'type-1',
      urgency: 'alta',
      status: 'pendente',
      created_at: '2026-06-01T10:00:00Z',
      author_id: 'user-1',
      photo_url: null,
      score: null,
    },
  }
}

vi.mock('@/store/workspaceStore', () => ({
  useWorkspaceStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({
      selectedIds,
      toggleSelect: mockToggleSelect,
      clearSelection: mockClearSelection,
    }),
}))

vi.mock('@/hooks/useFilteredReports', () => ({
  useFilteredReports: () => ({ features: [makeFeature(0), makeFeature(1)] }),
}))

vi.mock('@/hooks/useSimilarToSet', () => ({
  useSimilarToSet: () => ({ data: [], isLoading: false, error: null }),
}))

vi.mock('@/hooks/useForwardings', () => ({
  useCreateForwarding: () => ({ mutate: vi.fn(), isPending: false }),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient()
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
  selectedIds = new Set<string>(['report-0', 'report-1'])
})

describe('CestaView', () => {
  it('lists the selected reports', () => {
    render(<CestaView />, { wrapper })
    expect(screen.getByText('Relato número 0')).toBeTruthy()
    expect(screen.getByText('Relato número 1')).toBeTruthy()
    expect(screen.getByText(/Cesta de relatos \(2\)/)).toBeTruthy()
  })

  it('removing an item calls toggleSelect', () => {
    render(<CestaView />, { wrapper })
    const removeButtons = screen.getAllByRole('button', { name: /remover da cesta/i })
    fireEvent.click(removeButtons[0])
    expect(mockToggleSelect).toHaveBeenCalledWith('report-0')
  })

  it('"Limpar cesta" calls clearSelection', () => {
    render(<CestaView />, { wrapper })
    fireEvent.click(screen.getByRole('button', { name: /limpar cesta/i }))
    expect(mockClearSelection).toHaveBeenCalled()
  })

  it('opens the create forwarding dialog', () => {
    render(<CestaView />, { wrapper })
    fireEvent.click(screen.getByRole('button', { name: /criar encaminhamento \(2\)/i }))
    // Dialog title appears once opened
    expect(screen.getByText(/Criar encaminhamento \(2 relatos\)/)).toBeTruthy()
  })

  it('shows empty state when the basket is empty', () => {
    selectedIds = new Set<string>()
    render(<CestaView />, { wrapper })
    expect(screen.getByText(/Selecione relatos no mapa ou na tabela/)).toBeTruthy()
    expect(screen.queryByRole('button', { name: /criar encaminhamento/i })).toBeNull()
  })
})
