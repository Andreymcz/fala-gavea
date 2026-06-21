import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DateRangePresets } from './DateRangePresets'
import { useWorkspaceStore } from '@/store/workspaceStore'

// Reset store between tests
beforeEach(() => {
  useWorkspaceStore.setState({ draftFilters: {} })
})

function toISODate(d: Date): string {
  return d.toISOString().split('T')[0]
}

describe('DateRangePresets', () => {
  it('renders all preset buttons', () => {
    render(<DateRangePresets />)
    expect(screen.getByText('Hoje')).toBeTruthy()
    expect(screen.getByText('Últ. 7 dias')).toBeTruthy()
    expect(screen.getByText('Últ. 15 dias')).toBeTruthy()
    expect(screen.getByText('Últ. 30 dias')).toBeTruthy()
    expect(screen.getByText('Este mês')).toBeTruthy()
    expect(screen.getByText('Personalizado')).toBeTruthy()
  })

  it('selecting "Últ. 7 dias" calls setDraftFilter with correct since/until', () => {
    render(<DateRangePresets />)
    fireEvent.click(screen.getByText('Últ. 7 dias'))
    const { draftFilters } = useWorkspaceStore.getState()
    const today = new Date()
    const expectedUntil = toISODate(today)
    const d = new Date(today)
    d.setDate(d.getDate() - 6)
    const expectedSince = toISODate(d)
    expect(draftFilters.since).toBe(expectedSince)
    expect(draftFilters.until).toBe(expectedUntil)
  })

  it('selecting "Últ. 30 dias" sets since 29 days ago', () => {
    render(<DateRangePresets />)
    fireEvent.click(screen.getByText('Últ. 30 dias'))
    const { draftFilters } = useWorkspaceStore.getState()
    const today = new Date()
    const d = new Date(today)
    d.setDate(d.getDate() - 29)
    expect(draftFilters.since).toBe(toISODate(d))
    expect(draftFilters.until).toBe(toISODate(today))
  })

  it('selecting "Hoje" sets since and until to today', () => {
    render(<DateRangePresets />)
    fireEvent.click(screen.getByText('Hoje'))
    const { draftFilters } = useWorkspaceStore.getState()
    const today = toISODate(new Date())
    expect(draftFilters.since).toBe(today)
    expect(draftFilters.until).toBe(today)
  })

  it('selecting "Personalizado" shows native date inputs', () => {
    render(<DateRangePresets />)
    fireEvent.click(screen.getByText('Personalizado'))
    const inputs = screen.getAllByDisplayValue('')
    // Should find date inputs (they start empty)
    expect(inputs.length).toBeGreaterThanOrEqual(2)
    // Check they are type=date
    const dateInputs = document.querySelectorAll('input[type="date"]')
    expect(dateInputs.length).toBe(2)
  })

  it('"Personalizado" is auto-selected when draftFilters.since does not match any preset', () => {
    useWorkspaceStore.setState({ draftFilters: { since: '2020-01-01', until: '2020-06-01' } })
    render(<DateRangePresets />)
    const personalizado = screen.getByText('Personalizado').closest('button')
    expect(personalizado?.className).toContain('ring-2')
  })

  it('shows resolved absolute dates after selecting a preset (not Personalizado)', () => {
    render(<DateRangePresets />)
    fireEvent.click(screen.getByText('Hoje'))
    // Should show "De: DD/MM/YYYY Até: DD/MM/YYYY" somewhere
    expect(screen.getByText(/De:/)).toBeTruthy()
    expect(screen.getByText(/Até:/)).toBeTruthy()
  })

  it('custom date inputs update draftFilters.since when changed', () => {
    render(<DateRangePresets />)
    fireEvent.click(screen.getByText('Personalizado'))
    const dateInputs = document.querySelectorAll('input[type="date"]')
    fireEvent.change(dateInputs[0], { target: { value: '2024-03-15' } })
    const { draftFilters } = useWorkspaceStore.getState()
    expect(draftFilters.since).toBe('2024-03-15')
  })
})
