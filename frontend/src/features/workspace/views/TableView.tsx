import { useState, useEffect, useRef } from 'react'
import { useFilteredReports } from '@/hooks/useFilteredReports'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { useReportTypes } from '@/hooks/useReportTypes'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from '@/components/ui/dialog'

// ─── Types ──────────────────────────────────────────────────────────────────

type SortKey = 'text' | 'urgency' | 'status' | 'created_at' | 'score'
type SortDir = 'asc' | 'desc'

interface SortConfig {
  key: SortKey
  dir: SortDir
}

// ─── Constants ───────────────────────────────────────────────────────────────

const PAGE_SIZE = 50

// ─── Helpers ─────────────────────────────────────────────────────────────────

function urgencyLabel(u: string): string {
  if (u === 'alta') return '▲ Alta'
  if (u === 'media') return '● Média'
  return '▼ Baixa'
}

function urgencyOrder(u: string): number {
  if (u === 'alta') return 0
  if (u === 'media') return 1
  return 2
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

function statusOrder(s: string): number {
  const order: Record<string, number> = {
    pendente: 0,
    em_analise: 1,
    encaminhado: 2,
    resolvido: 3,
  }
  return order[s] ?? 99
}

function scoreColor(score: number): string {
  if (score >= 0.7) return 'text-green-600'
  if (score >= 0.4) return 'text-amber-600'
  return 'text-gray-400'
}

function scoreLabel(score: number): string {
  if (score >= 0.7) return '(alta)'
  if (score >= 0.4) return '(média)'
  return '(baixa)'
}

function sortIcon(key: SortKey, config: SortConfig | null): string {
  if (!config || config.key !== key) return '⇅'
  return config.dir === 'asc' ? '↑' : '↓'
}

function ariaSortValue(key: SortKey, config: SortConfig | null): 'ascending' | 'descending' | 'none' {
  if (!config || config.key !== key) return 'none'
  return config.dir === 'asc' ? 'ascending' : 'descending'
}

// ─── Component ───────────────────────────────────────────────────────────────

export function TableView() {
  const [sortConfig, setSortConfig] = useState<SortConfig | null>(null)
  const [page, setPage] = useState(0)
  const [dense, setDense] = useState(false)
  const [dialogFeatureId, setDialogFeatureId] = useState<string | null>(null)
  const dialogTriggerRef = useRef<HTMLButtonElement | null>(null)

  const filters = useWorkspaceStore((s) => s.filters)
  const selectedIds = useWorkspaceStore((s) => s.selectedIds)
  const toggleSelect = useWorkspaceStore((s) => s.toggleSelect)
  const setSimilarSeed = useWorkspaceStore((s) => s.setSimilarSeed)
  const { data: reportTypes = [] } = useReportTypes()
  const typeMap = new Map(reportTypes.map((rt) => [rt.id, rt.name]))

  const { features, total, isLoading, ranked_by } = useFilteredReports({
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
  })

  const showScore = ranked_by === 'similarity'
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  // Reset page when filters or sort change (serialize to avoid object identity issues)
  const filtersKey = JSON.stringify(filters)
  useEffect(() => {
    setPage(0)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtersKey])

  useEffect(() => {
    setPage(0)
  }, [sortConfig])

  // Sort features locally
  const sorted = Array.from(features).sort((a, b) => {
    if (!sortConfig) return 0
    const { key, dir } = sortConfig
    const mult = dir === 'asc' ? 1 : -1
    const pa = a.properties
    const pb = b.properties

    switch (key) {
      case 'text':
        return mult * pa.text.localeCompare(pb.text, 'pt-BR')
      case 'urgency':
        return mult * (urgencyOrder(pa.urgency) - urgencyOrder(pb.urgency))
      case 'status':
        return mult * (statusOrder(pa.status) - statusOrder(pb.status))
      case 'created_at':
        return mult * (pa.created_at < pb.created_at ? -1 : pa.created_at > pb.created_at ? 1 : 0)
      case 'score': {
        const sa = pa.score ?? null
        const sb = pb.score ?? null
        if (sa === null && sb === null) return 0
        if (sa === null) return 1   // nulls last
        if (sb === null) return -1
        return mult * (sa - sb)
      }
      default:
        return 0
    }
  })

  function handleSort(key: SortKey) {
    setSortConfig((prev) => {
      if (prev && prev.key === key) {
        return { key, dir: prev.dir === 'asc' ? 'desc' : 'asc' }
      }
      return { key, dir: 'asc' }
    })
  }

  const dialogFeature = dialogFeatureId ? sorted.find((f) => f.properties.id === dialogFeatureId) : null

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center text-sm text-gray-400">
        Carregando...
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Controls row */}
      <div className="flex items-center justify-between px-3 py-1 border-b border-gray-100">
        <span className="text-xs text-gray-500">
          {total} relatos encontrados — página {page + 1} de {totalPages}
        </span>
        <button
          className="text-xs px-2 py-1 rounded border border-gray-200 hover:bg-gray-50"
          onClick={() => setDense((d) => !d)}
          aria-pressed={dense}
        >
          {dense ? 'Confortável' : 'Compacto'}
        </button>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-10">
                <span className="sr-only">Selecionar</span>
              </TableHead>
              <TableHead aria-sort={ariaSortValue('text', sortConfig)}>
                <button
                  className="flex items-center gap-1 hover:text-gray-900"
                  onClick={() => handleSort('text')}
                  aria-label="Ordenar por Texto"
                >
                  Texto {sortIcon('text', sortConfig)}
                </button>
              </TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead aria-sort={ariaSortValue('urgency', sortConfig)}>
                <button
                  className="flex items-center gap-1 hover:text-gray-900"
                  onClick={() => handleSort('urgency')}
                  aria-label="Ordenar por Urgência"
                >
                  Urgência {sortIcon('urgency', sortConfig)}
                </button>
              </TableHead>
              <TableHead aria-sort={ariaSortValue('status', sortConfig)}>
                <button
                  className="flex items-center gap-1 hover:text-gray-900"
                  onClick={() => handleSort('status')}
                  aria-label="Ordenar por Status"
                >
                  Status {sortIcon('status', sortConfig)}
                </button>
              </TableHead>
              <TableHead aria-sort={ariaSortValue('created_at', sortConfig)}>
                <button
                  className="flex items-center gap-1 hover:text-gray-900"
                  onClick={() => handleSort('created_at')}
                  aria-label="Ordenar por Data"
                >
                  Data {sortIcon('created_at', sortConfig)}
                </button>
              </TableHead>
              {showScore && (
                <TableHead
                  aria-sort={ariaSortValue('score', sortConfig)}
                  title="Pontuação de similaridade semântica (0–1)"
                >
                  <button
                    className="flex items-center gap-1 hover:text-gray-900"
                    onClick={() => handleSort('score')}
                    aria-label="Ordenar por Relevância"
                  >
                    Relevância {sortIcon('score', sortConfig)}
                  </button>
                </TableHead>
              )}
              <TableHead><span className="sr-only">Ações</span></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.map((f) => {
              const p = f.properties
              const isSelected = selectedIds.has(p.id)
              const truncated = p.text.length > 80 ? p.text.slice(0, 80) + '…' : p.text
              return (
                <TableRow
                  key={p.id}
                  className={`${isSelected ? 'bg-blue-50' : ''} ${dense ? 'h-7' : 'h-10'}`}
                  onClick={() => toggleSelect(p.id)}
                  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleSelect(p.id) } }}
                  tabIndex={0}
                  style={{ cursor: 'pointer' }}
                  aria-selected={isSelected}
                >
                  <TableCell>
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleSelect(p.id)}
                      onClick={(e) => e.stopPropagation()}
                      aria-label={`Selecionar relato ${p.id.slice(0, 8)}`}
                    />
                  </TableCell>
                  <TableCell className="max-w-xs">
                    <span>{truncated}</span>{' '}
                    {p.text.length > 80 && (
                      <button
                        ref={(el) => {
                          if (dialogFeatureId === p.id) dialogTriggerRef.current = el
                        }}
                        className="text-xs text-blue-500 hover:underline"
                        onClick={(e) => { e.stopPropagation(); setDialogFeatureId(p.id) }}
                        aria-label={`Ler relato ${p.id.slice(0, 8)}`}
                      >
                        Ler relato
                      </button>
                    )}
                  </TableCell>
                  <TableCell>{typeMap.get(p.report_type_id) ?? '—'}</TableCell>
                  <TableCell>{urgencyLabel(p.urgency)}</TableCell>
                  <TableCell>{statusLabel(p.status)}</TableCell>
                  <TableCell className="text-xs">
                    {new Date(p.created_at).toLocaleDateString('pt-BR')}
                  </TableCell>
                  {showScore && (
                    <TableCell className={`text-xs font-mono ${p.score != null ? scoreColor(p.score) : 'text-gray-400'}`}>
                      {p.score != null ? (
                        <>
                          {p.score.toFixed(2)}
                          <span className="sr-only">{scoreLabel(p.score)}</span>
                        </>
                      ) : '—'}
                    </TableCell>
                  )}
                  <TableCell>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-xs h-7 px-2"
                      onClick={(e) => { e.stopPropagation(); setSimilarSeed(p.id) }}
                      aria-label={`Ver relatos similares a ${p.id.slice(0, 8)}`}
                    >
                      Similares
                    </Button>
                  </TableCell>
                </TableRow>
              )
            })}
            {sorted.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={showScore ? 8 : 7}
                  className="text-center text-sm text-gray-400"
                >
                  Nenhum relato encontrado.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-center gap-4 py-2 border-t border-gray-100 text-sm">
        <button
          className="px-3 py-1 rounded border border-gray-200 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
          onClick={() => setPage((p) => Math.max(0, p - 1))}
          disabled={page === 0}
          aria-label="Anterior"
        >
          ‹ Anterior
        </button>
        <span className="text-xs text-gray-500">
          Página {page + 1} de {totalPages}
        </span>
        <button
          className="px-3 py-1 rounded border border-gray-200 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
          onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
          disabled={page >= totalPages - 1}
          aria-label="Próxima"
        >
          Próxima ›
        </button>
      </div>

      {/* Full-text Dialog */}
      <Dialog
        open={dialogFeatureId !== null}
        onOpenChange={(open) => {
          if (!open) {
            setDialogFeatureId(null)
            dialogTriggerRef.current?.focus()
          }
        }}
      >
        <DialogContent>
          {dialogFeature && (() => {
            const p = dialogFeature.properties
            return (
              <>
                <DialogHeader>
                  <DialogTitle>Relato completo</DialogTitle>
                </DialogHeader>
                <div className="mt-4 space-y-4">
                  <p className="text-sm leading-relaxed">{p.text}</p>
                  <dl className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <dt className="text-xs text-gray-500 uppercase">Tipo</dt>
                      <dd>{typeMap.get(p.report_type_id) ?? '—'}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-gray-500 uppercase">Urgência</dt>
                      <dd>{urgencyLabel(p.urgency)}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-gray-500 uppercase">Status</dt>
                      <dd>{statusLabel(p.status)}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-gray-500 uppercase">Data</dt>
                      <dd>{new Date(p.created_at).toLocaleDateString('pt-BR')}</dd>
                    </div>
                  </dl>
                  <div className="flex justify-between pt-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setSimilarSeed(p.id)
                        setDialogFeatureId(null)
                      }}
                    >
                      Similares
                    </Button>
                    <DialogClose asChild>
                      <Button size="sm" variant="ghost">Fechar</Button>
                    </DialogClose>
                  </div>
                </div>
              </>
            )
          })()}
        </DialogContent>
      </Dialog>
    </div>
  )
}
