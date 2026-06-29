import { render, fireEvent, act, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const applyFilters = vi.fn()
const clearFilters = vi.fn()
const setDraftFilter = vi.fn()
const setSemanticQuery = vi.fn()
const togglePanel = vi.fn()
const setLoadedPresetName = vi.fn()
const setLoadedPresetId = vi.fn()
const setDraftFilterName = vi.fn()

let mockIsDirty = false
let mockPanelOpen = true
let mockLoadedPresetName: string | null = null
let mockLoadedPresetId: string | null = null
let mockDraftFilterName = ''
let mockFilters: Record<string, unknown> = {}
let mockNlSuggestion: Record<string, unknown> | null = null
let mockNlWarnings: string[] = []

const setNLSuggestion = vi.fn()
const applyNLSuggestion = vi.fn()

const getMockStore = (selector: (s: Record<string, unknown>) => unknown) => {
  const store = {
    filters: mockFilters,
    draftFilters: { semanticQuery: '' } as Record<string, unknown>,
    draftFilterName: mockDraftFilterName,
    setFilter: setDraftFilter,
    setDraftFilter,
    clearFilters,
    setSemanticQuery,
    applyFilters,
    togglePanel,
    panelOpen: mockPanelOpen,
    loadedPresetName: mockLoadedPresetName,
    loadedPresetId: mockLoadedPresetId,
    setLoadedPresetName,
    setLoadedPresetId,
    setDraftFilterName,
    isDirty: () => mockIsDirty,
    nlSuggestion: mockNlSuggestion,
    nlWarnings: mockNlWarnings,
    setNLSuggestion,
    applyNLSuggestion,
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

// Mock @tanstack/react-query
const mockInvalidateQueries = vi.fn()
const mockMutate = vi.fn()
let mockSavedFilters: Array<{ id: string; name: string; body: Record<string, unknown> }> = []
let mockListError = false
let mockListEnabled = false

vi.mock('@tanstack/react-query', () => ({
  useQuery: ({ enabled }: { enabled?: boolean }) => {
    mockListEnabled = !!enabled
    return {
      data: mockListEnabled ? mockSavedFilters : [],
      isError: mockListEnabled ? mockListError : false,
    }
  },
  useMutation: ({ onSuccess }: { onSuccess?: (data: unknown) => void }) => ({
    mutate: (arg: unknown) => {
      mockMutate(arg)
      if (onSuccess) onSuccess({ id: 'new-id', name: typeof arg === 'string' ? arg : 'test', body: {} })
    },
    isPending: false,
  }),
  useQueryClient: () => ({ invalidateQueries: mockInvalidateQueries }),
}))

// Mock api
vi.mock('@/lib/api', () => ({
  api: {
    listSavedFilters: vi.fn(() => Promise.resolve([])),
    getSavedFilter: vi.fn(() => Promise.resolve({ id: '1', name: 'test', body: {} })),
    createSavedFilter: vi.fn(() => Promise.resolve({ id: 'new-id', name: 'test', body: {} })),
    updateSavedFilter: vi.fn(() => Promise.resolve({ id: '1', name: 'test', body: {} })),
    deleteSavedFilter: vi.fn(() => Promise.resolve()),
  },
}))

// Mock auth
let mockToken: string | null = 'test-token'
vi.mock('@/auth/useAuth', () => ({
  useAuth: () => ({ token: mockToken, user: null, isLoading: false }),
}))

// Mock postNLFilter
const mockPostNLFilter = vi.fn()
vi.mock('@/api/nlFilter', () => ({
  postNLFilter: (...args: unknown[]) => mockPostNLFilter(...args),
}))

import { FilterPanel } from './FilterPanel'

beforeEach(() => {
  vi.resetAllMocks()
  mockIsDirty = false
  mockPanelOpen = true
  mockLoadedPresetName = null
  mockLoadedPresetId = null
  mockDraftFilterName = ''
  mockFilters = {}
  mockSavedFilters = []
  mockListError = false
  mockListEnabled = false
  mockToken = 'test-token'
  mockNlSuggestion = null
  mockNlWarnings = []
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

  it('Section 4 NL textarea renders enabled when token is present', () => {
    mockToken = 'test-token'
    const { getByPlaceholderText } = render(<FilterPanel />)
    const input = getByPlaceholderText(/Descreva o filtro/i)
    expect(input).toBeTruthy()
    expect((input as HTMLTextAreaElement).disabled).toBe(false)
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
    expect(queryByRole('button', { name: /Aplicar/i })).toBeNull()
    const toggle = getByRole('button', { name: /Expandir painel/i })
    expect(toggle).toBeTruthy()
  })

  // --- New preset bar tests ---

  it('Save popover appears on "Salvar" click', () => {
    const { getByRole, getByPlaceholderText } = render(<FilterPanel />)
    fireEvent.click(getByRole('button', { name: /^Salvar$/i }))
    expect(getByPlaceholderText(/Nome do filtro salvo/i)).toBeTruthy()
  })

  it('auto-name generated when draftFilterName is empty and filters are active', () => {
    mockDraftFilterName = ''
    mockFilters = { urgency: 'alta' }
    const { getByRole, getByDisplayValue } = render(<FilterPanel />)
    fireEvent.click(getByRole('button', { name: /^Salvar$/i }))
    // Auto-generated name should contain urgency label
    const input = getByDisplayValue(/Urgência/i)
    expect(input).toBeTruthy()
  })

  it('Load dropdown shows "Carregar" button that toggles dropdown', () => {
    mockSavedFilters = [{ id: '1', name: 'Meu filtro', body: {} }]
    const { getByRole, getByText } = render(<FilterPanel />)
    fireEvent.click(getByRole('button', { name: /^Carregar$/i }))
    expect(getByText('Meu filtro')).toBeTruthy()
  })

  it('Load dropdown shows error message when listError is true', () => {
    mockListError = true
    const { getByRole, getByText } = render(<FilterPanel />)
    fireEvent.click(getByRole('button', { name: /^Carregar$/i }))
    expect(getByText(/Erro ao carregar filtros salvos/i)).toBeTruthy()
  })

  it('Trash icon calls deleteMutation.mutate with the correct id', () => {
    mockSavedFilters = [{ id: 'abc', name: 'Filtro A', body: {} }]
    const { getByRole, getByTitle } = render(<FilterPanel />)
    fireEvent.click(getByRole('button', { name: /^Carregar$/i }))
    const trashBtn = getByTitle('Remover filtro')
    fireEvent.click(trashBtn)
    expect(mockMutate).toHaveBeenCalledWith('abc')
  })

  it('* appears in preset label when loadedPresetName is set and isDirty is true', () => {
    mockLoadedPresetName = 'Meu preset'
    mockIsDirty = true
    const { getByText } = render(<FilterPanel />)
    expect(getByText('Meu preset *')).toBeTruthy()
  })

  it('preset label shows name without * when not dirty', () => {
    mockLoadedPresetName = 'Meu preset'
    mockIsDirty = false
    const { getByText } = render(<FilterPanel />)
    expect(getByText('Meu preset')).toBeTruthy()
  })

  it('shows "Sem filtro salvo" when no preset is loaded', () => {
    mockLoadedPresetName = null
    const { getByText } = render(<FilterPanel />)
    expect(getByText('Sem filtro salvo')).toBeTruthy()
  })

  it('"Atualizar" option appears in save popover when loadedPresetId is set', () => {
    mockLoadedPresetId = 'preset-123'
    const { getByRole } = render(<FilterPanel />)
    fireEvent.click(getByRole('button', { name: /^Salvar$/i }))
    expect(getByRole('button', { name: /Atualizar/i })).toBeTruthy()
  })

  // --- Section 4: NL assistant tests ---

  it('Section 4 submit button triggers postNLFilter', async () => {
    mockPostNLFilter.mockResolvedValueOnce({ body: { urgency: 'alta' }, warnings: [] })
    const { getByPlaceholderText } = render(<FilterPanel />)
    const textarea = getByPlaceholderText(/Descreva o filtro/i)
    fireEvent.change(textarea, { target: { value: 'postes apagados' } })
    await act(async () => {
      fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter', shiftKey: false })
    })
    expect(mockPostNLFilter).toHaveBeenCalledWith('postes apagados', 'test-token')
  })

  it('suggestion preview zone appears after successful response', async () => {
    // Pre-set suggestion in store to simulate a successful response
    mockNlSuggestion = { urgency: 'alta' }
    const { getByRole } = render(<FilterPanel />)
    expect(getByRole('button', { name: /Aplicar sugestão ao rascunho/i })).toBeTruthy()
    expect(getByRole('button', { name: /Descartar/i })).toBeTruthy()
  })

  it('"Aplicar sugestão ao rascunho" calls applyNLSuggestion', () => {
    mockNlSuggestion = { urgency: 'alta' }
    const { getByRole } = render(<FilterPanel />)
    fireEvent.click(getByRole('button', { name: /Aplicar sugestão ao rascunho/i }))
    expect(applyNLSuggestion).toHaveBeenCalledWith(mockNlSuggestion)
  })

  it('"Descartar" clears suggestion', () => {
    mockNlSuggestion = { urgency: 'alta' }
    const { getByRole } = render(<FilterPanel />)
    fireEvent.click(getByRole('button', { name: /Descartar/i }))
    expect(setNLSuggestion).toHaveBeenCalledWith(null, [])
  })

  it('unavailable error shows graceful degradation message', async () => {
    const ref: { reject?: (e: Error) => void } = {}
    const { getByPlaceholderText } = render(<FilterPanel />)
    const textarea = getByPlaceholderText(/Descreva o filtro/i)
    fireEvent.change(textarea, { target: { value: 'teste' } })
    await act(async () => {
      mockPostNLFilter.mockImplementationOnce(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        () => new Promise<any>((_, reject) => { ref.reject = reject }),
      )
      fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter', shiftKey: false })
    })
    expect(mockPostNLFilter).toHaveBeenCalled()
    expect(ref.reject).toBeDefined()
    await act(async () => {
      ref.reject!(new Error('unavailable'))
      await Promise.resolve()
      await Promise.resolve()
    })
    expect(screen.getByText(/indispon/i)).toBeTruthy()
  })

  it('rate_limit error shows rate limit message', async () => {
    const ref: { reject?: (e: Error) => void } = {}
    const { getByPlaceholderText } = render(<FilterPanel />)
    const textarea = getByPlaceholderText(/Descreva o filtro/i)
    fireEvent.change(textarea, { target: { value: 'teste' } })
    await act(async () => {
      mockPostNLFilter.mockImplementationOnce(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        () => new Promise<any>((_, reject) => { ref.reject = reject }),
      )
      fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter', shiftKey: false })
    })
    expect(mockPostNLFilter).toHaveBeenCalled()
    expect(ref.reject).toBeDefined()
    await act(async () => {
      ref.reject!(new Error('rate_limit'))
      await Promise.resolve()
      await Promise.resolve()
    })
    expect(screen.getByText(/Limite de/i)).toBeTruthy()
  })
})
