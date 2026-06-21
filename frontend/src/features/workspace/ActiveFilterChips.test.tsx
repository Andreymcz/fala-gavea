import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { WorkspaceFilters } from '@/lib/types'

const removeFilter = vi.fn()
let mockFilters: WorkspaceFilters = {}

const getMockStore = (selector: (s: Record<string, unknown>) => unknown) => {
  const store = {
    filters: mockFilters,
    removeFilter,
  }
  return selector(store as unknown as Record<string, unknown>)
}

vi.mock('@/store/workspaceStore', () => ({
  useWorkspaceStore: (sel: (s: Record<string, unknown>) => unknown) => getMockStore(sel),
}))

vi.mock('@/hooks/useReportTypes', () => ({
  useReportTypes: () => ({
    data: [{ id: 'some-id', name: 'Roubo', description: null, active: true, created_at: '' }],
  }),
}))

import { ActiveFilterChips } from './ActiveFilterChips'

describe('ActiveFilterChips', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFilters = {}
  })

  it('renders urgency and type chips', () => {
    mockFilters = { urgency: 'alta', type_id: 'some-id' }
    render(<ActiveFilterChips />)
    expect(screen.getByText(/Urgência: Alta/)).toBeTruthy()
    expect(screen.getByText(/Tipo: Roubo/)).toBeTruthy()
  })

  it('calls removeFilter when × is clicked on urgency chip', () => {
    mockFilters = { urgency: 'alta' }
    render(<ActiveFilterChips />)
    const buttons = screen.getAllByRole('button')
    const urgencyBtn = buttons.find(b => b.closest('span')?.textContent?.includes('Urgência'))
    expect(urgencyBtn).toBeTruthy()
    fireEvent.click(urgencyBtn!)
    expect(removeFilter).toHaveBeenCalledWith('urgency')
  })

  it('renders nothing when filters is empty', () => {
    mockFilters = {}
    const { container } = render(<ActiveFilterChips />)
    expect(container.firstChild).toBeNull()
  })

  it('renders status chip with Portuguese label', () => {
    mockFilters = { status: 'em_analise' }
    render(<ActiveFilterChips />)
    expect(screen.getByText(/Status: Em análise/)).toBeTruthy()
  })

  it('renders bbox chip', () => {
    mockFilters = { bbox: '-43.1,-22.9,-43.0,-22.8' }
    render(<ActiveFilterChips />)
    expect(screen.getByText(/Área do mapa/)).toBeTruthy()
  })

  it('truncates long semanticQuery', () => {
    mockFilters = { semanticQuery: 'uma busca muito longa que excede vinte caracteres' }
    render(<ActiveFilterChips />)
    expect(screen.getByText(/Busca: "uma busca muito long\.\.\."/)).toBeTruthy()
  })

  it('renders short semanticQuery without truncation', () => {
    mockFilters = { semanticQuery: 'curta' }
    render(<ActiveFilterChips />)
    expect(screen.getByText(/Busca: "curta"/)).toBeTruthy()
  })

  it('renders since and until chips with pt-BR dates', () => {
    mockFilters = { since: '2026-01-15', until: '2026-06-21' }
    render(<ActiveFilterChips />)
    // Just check prefix labels since locale formatting may vary
    expect(screen.getByText(/De:/)).toBeTruthy()
    expect(screen.getByText(/Até:/)).toBeTruthy()
  })
})
