import { useFilteredReports } from '@/hooks/useFilteredReports'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { useReportTypes } from '@/hooks/useReportTypes'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

function urgencyLabel(u: string): string {
  if (u === 'alta') return '▲ Alta'
  if (u === 'media') return '● Média'
  return '▼ Baixa'
}

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    pendente: 'Pendente',
    em_analise: 'Em análise',
    encaminhado: 'Encaminhado',
    resolvido: 'Resolvido',
  }
  return map[s] ?? s
}

export function TableView() {
  const { features, isLoading } = useFilteredReports()
  const { selectedIds, toggleSelect } = useWorkspaceStore((s) => ({
    selectedIds: s.selectedIds,
    toggleSelect: s.toggleSelect,
  }))
  const { data: reportTypes = [] } = useReportTypes()
  const typeMap = new Map(reportTypes.map((rt) => [rt.id, rt.name]))

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center text-sm text-gray-400">
        Carregando...
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-10">
              <span className="sr-only">Selecionar</span>
            </TableHead>
            <TableHead>Texto</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead>Urgência</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Data</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {features.map((f) => {
            const p = f.properties
            const isSelected = selectedIds.has(p.id)
            return (
              <TableRow
                key={p.id}
                className={isSelected ? 'bg-blue-50' : ''}
                onClick={() => toggleSelect(p.id)}
                style={{ cursor: 'pointer' }}
              >
                <TableCell>
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleSelect(p.id)}
                    onClick={(e) => e.stopPropagation()}
                    aria-label="Selecionar relato"
                  />
                </TableCell>
                <TableCell className="max-w-xs truncate">
                  {p.text.slice(0, 80)}
                </TableCell>
                <TableCell>{typeMap.get(p.report_type_id) ?? '—'}</TableCell>
                <TableCell>{urgencyLabel(p.urgency)}</TableCell>
                <TableCell>{statusLabel(p.status)}</TableCell>
                <TableCell className="text-xs">
                  {new Date(p.created_at).toLocaleDateString('pt-BR')}
                </TableCell>
              </TableRow>
            )
          })}
          {features.length === 0 && (
            <TableRow>
              <TableCell
                colSpan={6}
                className="text-center text-sm text-gray-400"
              >
                Nenhum relato encontrado.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  )
}
