import { useWorkspaceStore } from '@/store/workspaceStore'
import { useReportTypes } from '@/hooks/useReportTypes'
import type { WorkspaceFilters } from '@/lib/types'

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

function formatDate(iso: string): string {
  // iso is 'YYYY-MM-DD'; parse as local date to avoid UTC offset issues
  const [year, month, day] = iso.split('-').map(Number)
  const d = new Date(year, month - 1, day)
  return d.toLocaleDateString('pt-BR')
}

export function ActiveFilterChips() {
  const filters = useWorkspaceStore((s) => s.filters)
  const removeFilter = useWorkspaceStore((s) => s.removeFilter)
  const { data: reportTypes } = useReportTypes()

  type FilterKey = keyof WorkspaceFilters

  function getLabel(key: FilterKey, value: string): string {
    switch (key) {
      case 'type_id': {
        const found = reportTypes?.find((t) => t.id === value)
        return `Tipo: ${found ? found.name : value}`
      }
      case 'urgency':
        return `Urgência: ${URGENCY_LABELS[value] ?? value}`
      case 'status':
        return `Status: ${STATUS_LABELS[value] ?? value}`
      case 'since':
        return `De: ${formatDate(value)}`
      case 'until':
        return `Até: ${formatDate(value)}`
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

  const activeEntries = (Object.entries(filters) as [FilterKey, string | undefined][]).filter(
    ([, v]) => v !== undefined && v !== '',
  )

  if (activeEntries.length === 0) return null

  return (
    <div aria-live="polite" className="flex flex-wrap">
      {activeEntries.map(([key, value]) => (
        <span
          key={key}
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 text-xs mr-1 mb-1"
        >
          {getLabel(key, value as string)}
          <button
            type="button"
            aria-label={`Remover filtro ${key}`}
            className="text-blue-600 hover:text-blue-900 focus:outline-none"
            onClick={() => removeFilter(key)}
          >
            ×
          </button>
        </span>
      ))}
    </div>
  )
}
