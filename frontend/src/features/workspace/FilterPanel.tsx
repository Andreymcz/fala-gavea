import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { useReportTypes } from '@/hooks/useReportTypes'
import { useFilteredReports } from '@/hooks/useFilteredReports'
import type { Urgency, ReportStatus, WorkspaceFilters } from '@/lib/types'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ActiveFilterChips } from './ActiveFilterChips'
import { DateRangePresets } from './DateRangePresets'
import { api } from '@/lib/api'
import { useAuth } from '@/auth/useAuth'
import { postNLFilter } from '@/api/nlFilter'

const URGENCY_LABELS: Record<string, string> = {
  alta: 'Alta',
  media: 'Média',
  baixa: 'Baixa',
}

const STATUS_LABELS: Record<string, string> = {
  pendente: 'Pendente',
  em_analise: 'Em análise',
  encaminhado: 'Encaminhado',
  resolvido: 'Resolvido',
}

function getChipLabel(key: keyof WorkspaceFilters, value: string): string {
  switch (key) {
    case 'urgency':
      return `Urgência: ${URGENCY_LABELS[value] ?? value}`
    case 'status':
      return `Status: ${STATUS_LABELS[value] ?? value}`
    case 'since':
      return `De: ${value}`
    case 'until':
      return `Até: ${value}`
    case 'bbox':
      return 'Área do mapa'
    case 'semanticQuery': {
      const q = value.length > 20 ? value.slice(0, 20) + '...' : value
      return `Busca: "${q}"`
    }
    default:
      return `${key}: ${value}`
  }
}

export function FilterPanel() {
  const draftFilters = useWorkspaceStore((s) => s.draftFilters)
  const filters = useWorkspaceStore((s) => s.filters)
  const draftFilterName = useWorkspaceStore((s) => s.draftFilterName)
  const setDraftFilter = useWorkspaceStore((s) => s.setDraftFilter)
  const applyFilters = useWorkspaceStore((s) => s.applyFilters)
  const clearFilters = useWorkspaceStore((s) => s.clearFilters)
  const setSemanticQuery = useWorkspaceStore((s) => s.setSemanticQuery)
  const togglePanel = useWorkspaceStore((s) => s.togglePanel)
  const panelOpen = useWorkspaceStore((s) => s.panelOpen)
  const loadedPresetName = useWorkspaceStore((s) => s.loadedPresetName)
  const loadedPresetId = useWorkspaceStore((s) => s.loadedPresetId)
  const setLoadedPresetName = useWorkspaceStore((s) => s.setLoadedPresetName)
  const setLoadedPresetId = useWorkspaceStore((s) => s.setLoadedPresetId)
  const setDraftFilterName = useWorkspaceStore((s) => s.setDraftFilterName)
  const isDirty = useWorkspaceStore((s) => s.isDirty())
  const nlSuggestion = useWorkspaceStore((s) => s.nlSuggestion)
  const nlWarnings = useWorkspaceStore((s) => s.nlWarnings)
  const setNLSuggestion = useWorkspaceStore((s) => s.setNLSuggestion)
  const applyNLSuggestion = useWorkspaceStore((s) => s.applyNLSuggestion)

  const { token, user } = useAuth()

  const { data: reportTypes = [] } = useReportTypes()
  const { count } = useFilteredReports()
  const queryClient = useQueryClient()

  const [saveOpen, setSaveOpen] = useState(false)
  const [loadOpen, setLoadOpen] = useState(false)
  const [saveNameInput, setSaveNameInput] = useState('')
  const [nlText, setNlText] = useState('')
  const [nlLoading, setNlLoading] = useState(false)
  const [nlError, setNlError] = useState<string | null>(null)

  // Preset bar display name
  const presetLabel = loadedPresetName
    ? isDirty
      ? `${loadedPresetName} *`
      : loadedPresetName
    : 'Sem filtro salvo'

  const countLabel = `${count} relato${count !== 1 ? 's' : ''}`

  // Auto-generate name from active filter chips
  function autoName(): string {
    const entries = (Object.entries(filters) as [keyof WorkspaceFilters, string | undefined][]).filter(
      ([, v]) => v !== undefined && v !== '',
    )
    const parts = entries.map(([k, v]) => getChipLabel(k, v as string))
    const joined = parts.join(', ')
    return joined.length > 40 ? joined.slice(0, 40) : joined
  }

  function handleOpenSave() {
    setSaveNameInput(draftFilterName || autoName())
    setSaveOpen(true)
    setLoadOpen(false)
  }

  function handleOpenLoad() {
    setLoadOpen((prev) => !prev)
    setSaveOpen(false)
  }

  // List query
  const { data: savedFilters = [], isError: listError } = useQuery({
    queryKey: ['saved-filters'],
    queryFn: () => api.listSavedFilters(),
    staleTime: 30_000,
    enabled: loadOpen,
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (name: string) =>
      api.createSavedFilter({ name, body: filters }),
    onSuccess: (saved) => {
      setLoadedPresetName(saved.name)
      setLoadedPresetId(saved.id)
      setDraftFilterName(saved.name)
      void queryClient.invalidateQueries({ queryKey: ['saved-filters'] })
      setSaveOpen(false)
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: () =>
      api.updateSavedFilter(loadedPresetId!, { body: filters }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['saved-filters'] })
      setSaveOpen(false)
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteSavedFilter(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['saved-filters'] })
    },
  })

  // Load a preset
  async function handleLoadPreset(id: string, name: string) {
    const saved = await api.getSavedFilter(id)
    setDraftFilter(saved.body as Partial<typeof draftFilters>)
    setLoadedPresetName(name)
    setLoadedPresetId(id)
    setDraftFilterName(name)
    setLoadOpen(false)
  }

  async function handleNLSubmit() {
    if (!nlText.trim() || !token) return
    setNlLoading(true)
    setNlError(null)
    try {
      const result = await postNLFilter(nlText.trim(), token)
      setNLSuggestion(result.body as Partial<WorkspaceFilters>, result.warnings)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'error'
      if (msg === 'rate_limit') setNlError('Limite de requisições atingido. Tente novamente em instantes.')
      else if (msg === 'unavailable') setNlError('Assistente de IA indisponível no momento.')
      else setNlError('Erro ao processar. Tente novamente.')
    } finally {
      setNlLoading(false)
    }
  }

  function getSuggestionChips(suggestion: Partial<WorkspaceFilters>): string[] {
    const chips: string[] = []
    if (suggestion.urgency) chips.push(`Urgência: ${URGENCY_LABELS[suggestion.urgency] ?? suggestion.urgency}`)
    if (suggestion.status) chips.push(`Status: ${STATUS_LABELS[suggestion.status] ?? suggestion.status}`)
    if (suggestion.since) chips.push(`De: ${suggestion.since}`)
    if (suggestion.until) chips.push(`Até: ${suggestion.until}`)
    if (suggestion.semanticQuery) chips.push(`Busca: "${suggestion.semanticQuery}"`)
    if (suggestion.type_id) chips.push(`Tipo: ${suggestion.type_id}`)
    return chips
  }

  // Collapsed state
  if (!panelOpen) {
    return (
      <div className="relative flex flex-col items-center py-2">
        <button
          aria-label={`Expandir painel de filtros — ${countLabel}`}
          onClick={togglePanel}
          className="w-8 h-8 flex items-center justify-center rounded border border-gray-200 bg-white text-gray-500 hover:bg-gray-50 relative"
        >
          ›
          {(isDirty || count > 0) && (
            <span className="absolute -top-1 -right-1 text-[10px] bg-amber-500 text-white rounded-full w-4 h-4 flex items-center justify-center leading-none">
              {isDirty ? '!' : count}
            </span>
          )}
        </button>
      </div>
    )
  }

  const hasCommittedFilters = Object.keys(filters).some(
    (k) => filters[k as keyof typeof filters] !== undefined,
  )

  return (
    <div className="w-72 flex flex-col h-full bg-white border-r border-gray-200">
      {/* Section 1 — Preset bar */}
      <div className="border-b py-2 px-3 flex items-center gap-2 relative">
        <span className="text-xs font-medium text-gray-700 flex-1 truncate" title={presetLabel}>
          {presetLabel}
        </span>
        <button
          className="text-xs text-blue-600 hover:text-blue-800"
          onClick={handleOpenSave}
        >
          Salvar
        </button>
        <button
          className="text-xs text-blue-600 hover:text-blue-800"
          onClick={handleOpenLoad}
        >
          Carregar
        </button>
        <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
          {countLabel}
        </span>
        <button
          aria-label="Recolher painel de filtros"
          onClick={togglePanel}
          className="text-gray-400 hover:text-gray-600 ml-1"
        >
          ‹
        </button>

        {/* Save popover */}
        {saveOpen && (
          <div className="absolute top-full left-0 right-0 z-20 bg-white border border-gray-200 shadow-lg rounded p-3 flex flex-col gap-2">
            <p className="text-xs font-medium text-gray-700">Nome do filtro</p>
            <Input
              className="h-7 text-xs"
              value={saveNameInput}
              onChange={(e) => setSaveNameInput(e.target.value)}
              placeholder="Nome do filtro salvo"
              autoFocus
            />
            <div className="flex gap-2">
              <Button
                size="sm"
                className="flex-1 h-7 text-xs"
                onClick={() => createMutation.mutate(saveNameInput)}
                disabled={!saveNameInput.trim() || createMutation.isPending}
              >
                Confirmar
              </Button>
              {loadedPresetId && (
                <Button
                  size="sm"
                  variant="ghost"
                  className="flex-1 h-7 text-xs"
                  onClick={() => updateMutation.mutate()}
                  disabled={updateMutation.isPending}
                >
                  Atualizar
                </Button>
              )}
              <Button
                size="sm"
                variant="ghost"
                className="h-7 text-xs"
                onClick={() => setSaveOpen(false)}
              >
                Cancelar
              </Button>
            </div>
          </div>
        )}

        {/* Load dropdown */}
        {loadOpen && (
          <div className="absolute top-full left-0 right-0 z-20 bg-white border border-gray-200 shadow-lg rounded flex flex-col max-h-48 overflow-y-auto">
            {listError ? (
              <p className="text-xs text-red-600 px-3 py-2">Erro ao carregar filtros salvos</p>
            ) : savedFilters.length === 0 ? (
              <p className="text-xs text-gray-400 px-3 py-2">Nenhum filtro salvo.</p>
            ) : (
              savedFilters.map((sf) => (
                <div key={sf.id} className="flex items-center px-3 py-1.5 hover:bg-gray-50 gap-1">
                  <button
                    className="text-xs text-gray-700 flex-1 text-left truncate"
                    onClick={() => void handleLoadPreset(sf.id, sf.name)}
                  >
                    {sf.name}
                  </button>
                  <button
                    title="Remover filtro"
                    aria-label={`Remover filtro ${sf.name}`}
                    className="text-gray-400 hover:text-red-600 text-xs px-1"
                    onClick={() => deleteMutation.mutate(sf.id)}
                  >
                    🗑
                  </button>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Section 2 — Active chips */}
      <div className="border-b py-2 px-3 max-h-20 overflow-y-auto">
        <ActiveFilterChips />
        {!hasCommittedFilters && (
          <p className="text-xs text-gray-400">Nenhum filtro ativo.</p>
        )}
      </div>

      {/* Section 3 — Draft controls */}
      <div className="flex-1 overflow-y-auto py-2 px-3 flex flex-col gap-3">
        <div className="space-y-1">
          <Label className="text-xs">Tipo</Label>
          <Select
            value={draftFilters.type_id ?? '__all__'}
            onValueChange={(v) => setDraftFilter({ type_id: v === '__all__' ? undefined : v })}
          >
            <SelectTrigger className="h-8 text-xs">
              <SelectValue placeholder="Todos os tipos" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">Todos os tipos</SelectItem>
              {reportTypes.map((rt) => (
                <SelectItem key={rt.id} value={rt.id}>
                  {rt.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1">
          <Label className="text-xs">Urgência</Label>
          <Select
            value={draftFilters.urgency ?? '__all__'}
            onValueChange={(v) =>
              setDraftFilter({ urgency: v === '__all__' ? undefined : (v as Urgency) })
            }
          >
            <SelectTrigger className="h-8 text-xs">
              <SelectValue placeholder="Todas" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">Todas</SelectItem>
              <SelectItem value="alta">Alta</SelectItem>
              <SelectItem value="media">Média</SelectItem>
              <SelectItem value="baixa">Baixa</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1">
          <Label className="text-xs">Status</Label>
          <Select
            value={draftFilters.status ?? '__all__'}
            onValueChange={(v) =>
              setDraftFilter({ status: v === '__all__' ? undefined : (v as ReportStatus) })
            }
          >
            <SelectTrigger className="h-8 text-xs">
              <SelectValue placeholder="Todos" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">Todos</SelectItem>
              <SelectItem value="pendente">Pendente</SelectItem>
              <SelectItem value="em_analise">Em análise</SelectItem>
              <SelectItem value="encaminhado">Encaminhado</SelectItem>
              <SelectItem value="resolvido">Resolvido</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {user && (
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={draftFilters.author_id === user.id}
              onChange={(e) =>
                setDraftFilter({ author_id: e.target.checked ? user.id : undefined })
              }
              className="h-4 w-4"
            />
            <span className="text-xs text-gray-700">Meus relatos</span>
          </label>
        )}

        <DateRangePresets />

        <div className="space-y-1">
          <Label className="text-xs">Busca semântica</Label>
          <Input
            className="h-8 text-xs"
            placeholder="Descreva o que procura..."
            value={draftFilters.semanticQuery ?? ''}
            onChange={(e) => setSemanticQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') applyFilters()
            }}
          />
        </div>

        {isDirty && (
          <p aria-live="polite" className="text-xs text-amber-600">
            Filtros alterados — clique Aplicar
          </p>
        )}

        <Button
          size="sm"
          className="w-full"
          onClick={applyFilters}
          disabled={!isDirty}
        >
          Aplicar
        </Button>

        <Button
          size="sm"
          variant="ghost"
          className="w-full"
          onClick={clearFilters}
        >
          Limpar
        </Button>
      </div>

      {/* Section 4 — NL assistant footer */}
      <div className="border-t py-2 px-3 flex flex-col gap-1.5">
        <p className="text-xs text-gray-500 font-medium">Assistente de filtros</p>
        <div className="flex gap-1">
          <textarea
            className="flex-1 text-xs border border-gray-200 rounded px-2 py-1 resize-none focus:outline-none focus:ring-1 focus:ring-blue-400 disabled:opacity-50"
            rows={2}
            placeholder="Descreva o filtro em linguagem natural..."
            value={nlText}
            onChange={(e) => setNlText(e.target.value)}
            disabled={nlLoading}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                void handleNLSubmit()
              }
            }}
          />
          <Button
            size="sm"
            variant="ghost"
            className="h-auto px-2 text-xs self-end"
            onClick={() => void handleNLSubmit()}
            disabled={nlLoading || !nlText.trim()}
            title="Enviar"
          >
            {nlLoading ? '...' : '→'}
          </Button>
        </div>
        {nlError && (
          <p className="text-xs text-red-600">{nlError}</p>
        )}
        {nlSuggestion && (
          <div className="flex flex-col gap-1 mt-0.5">
            <div className="flex flex-wrap gap-1">
              {getSuggestionChips(nlSuggestion).map((chip) => (
                <span key={chip} className="text-xs bg-blue-50 text-blue-700 border border-blue-200 rounded px-1.5 py-0.5">
                  {chip}
                </span>
              ))}
              {nlWarnings.map((w, i) => (
                <span key={i} className="text-xs bg-amber-50 text-amber-700 border border-amber-200 rounded px-1.5 py-0.5">
                  ⚠ {w}
                </span>
              ))}
            </div>
            <div className="flex gap-1">
              <Button
                size="sm"
                className="flex-1 h-6 text-xs"
                onClick={() => {
                  applyNLSuggestion(nlSuggestion)
                  setNLSuggestion(null, [])
                  setNlText('')
                }}
              >
                Aplicar sugestão ao rascunho
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-6 text-xs"
                onClick={() => setNLSuggestion(null, [])}
              >
                Descartar
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
