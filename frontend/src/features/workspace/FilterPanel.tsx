import { useWorkspaceStore } from '@/store/workspaceStore'
import { useReportTypes } from '@/hooks/useReportTypes'
import { useFilteredReports } from '@/hooks/useFilteredReports'
import type { Urgency, ReportStatus } from '@/lib/types'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ActiveFilterChips } from './ActiveFilterChips'
import { DateRangePresets } from './DateRangePresets'

export function FilterPanel() {
  const draftFilters = useWorkspaceStore((s) => s.draftFilters)
  const filters = useWorkspaceStore((s) => s.filters)
  const setDraftFilter = useWorkspaceStore((s) => s.setDraftFilter)
  const applyFilters = useWorkspaceStore((s) => s.applyFilters)
  const clearFilters = useWorkspaceStore((s) => s.clearFilters)
  const setSemanticQuery = useWorkspaceStore((s) => s.setSemanticQuery)
  const togglePanel = useWorkspaceStore((s) => s.togglePanel)
  const panelOpen = useWorkspaceStore((s) => s.panelOpen)
  const loadedPresetName = useWorkspaceStore((s) => s.loadedPresetName)
  const isDirty = useWorkspaceStore((s) => s.isDirty())

  const { data: reportTypes = [] } = useReportTypes()
  const { count } = useFilteredReports()

  // Preset bar display name
  const presetLabel = loadedPresetName
    ? isDirty
      ? `${loadedPresetName} *`
      : loadedPresetName
    : 'Sem nome'

  const countLabel = `${count} relato${count !== 1 ? 's' : ''}`

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
      <div className="border-b py-2 px-3 flex items-center gap-2">
        <span className="text-xs font-medium text-gray-700 flex-1 truncate" title={presetLabel}>
          {presetLabel}
        </span>
        <button
          className="text-xs text-gray-400 opacity-50 cursor-not-allowed"
          disabled
          title="Disponível em breve"
        >
          Salvar
        </button>
        <button
          className="text-xs text-gray-400 opacity-50 cursor-not-allowed"
          disabled
          title="Disponível em breve"
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
      <div className="border-t py-2 px-3">
        <p className="text-xs text-gray-500 font-medium mb-1">Assistente de filtros</p>
        <div className="flex gap-1">
          <Input
            placeholder="Descreva o filtro..."
            className="h-7 text-xs flex-1"
            disabled
          />
          <Button
            size="sm"
            variant="ghost"
            className="h-7 px-2 text-xs"
            disabled
            title="Disponível em breve"
          >
            →
          </Button>
        </div>
        <p className="text-xs text-gray-400 mt-1">Em breve: filtros por linguagem natural</p>
      </div>
    </div>
  )
}
