import { useMemo, useState } from 'react'
import { useQueries } from '@tanstack/react-query'
import { api, ApiError } from '@/lib/api'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { useFilteredReports } from '@/hooks/useFilteredReports'
import { useSimilarToSet } from '@/hooks/useSimilarToSet'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CreateForwardingDialog } from '@/features/map/CreateForwardingDialog'
import type { ReportDetail, Urgency } from '@/lib/types'

function urgencyLabel(u: Urgency): string {
  if (u === 'alta') return '▲ Alta'
  if (u === 'media') return '● Média'
  return '▼ Baixa'
}

interface BasketItem {
  id: string
  text: string
  urgency: Urgency
}

export function CestaView() {
  const selectedIds = useWorkspaceStore((s) => s.selectedIds)
  const toggleSelect = useWorkspaceStore((s) => s.toggleSelect)
  const clearSelection = useWorkspaceStore((s) => s.clearSelection)

  const { features } = useFilteredReports()
  const [showCreateDialog, setShowCreateDialog] = useState(false)

  const selectedArray = useMemo(() => Array.from(selectedIds), [selectedIds])

  // Hydrate from the current filtered features cache.
  const cached = useMemo(() => {
    const map = new Map<string, BasketItem>()
    for (const f of features) {
      if (selectedIds.has(f.properties.id)) {
        map.set(f.properties.id, {
          id: f.properties.id,
          text: f.properties.text,
          urgency: f.properties.urgency,
        })
      }
    }
    return map
  }, [features, selectedIds])

  // Any selected id NOT in the current filter — fetch by id so the basket is accurate.
  const missingIds = useMemo(
    () => selectedArray.filter((id) => !cached.has(id)),
    [selectedArray, cached],
  )

  const missingQueries = useQueries({
    queries: missingIds.map((id) => ({
      queryKey: ['report', id],
      queryFn: () => api.getReport(id),
      staleTime: 30_000,
    })),
  })

  const items: BasketItem[] = useMemo(() => {
    const fetched = new Map<string, BasketItem>()
    missingQueries.forEach((q) => {
      const d = q.data as ReportDetail | undefined
      if (d) fetched.set(d.id, { id: d.id, text: d.text, urgency: d.urgency })
    })
    return selectedArray.map(
      (id) =>
        cached.get(id) ??
        fetched.get(id) ?? { id, text: 'Carregando relato…', urgency: 'baixa' as Urgency },
    )
  }, [selectedArray, cached, missingQueries])

  const similar = useSimilarToSet(selectedArray)

  const isEmpty = selectedArray.length === 0

  return (
    <div className="flex flex-col gap-3 p-4 overflow-auto">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-gray-700">
          Cesta de relatos ({selectedArray.length})
        </h3>
        {!isEmpty && (
          <Button size="sm" variant="ghost" onClick={clearSelection}>
            Limpar cesta
          </Button>
        )}
      </div>

      {isEmpty && (
        <div role="status" className="text-xs text-gray-400">
          Selecione relatos no mapa ou na tabela para montar a cesta e criar um encaminhamento.
        </div>
      )}

      {!isEmpty && (
        <>
          <ul className="space-y-2">
            {items.map((item) => (
              <li
                key={item.id}
                className="flex items-start justify-between gap-2 rounded-md border border-gray-200 p-2 text-xs"
              >
                <div className="min-w-0">
                  <div className="text-gray-700 line-clamp-2">{item.text}</div>
                  <Badge variant={`urgency-${item.urgency}`} className="mt-1">
                    {urgencyLabel(item.urgency)}
                  </Badge>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  aria-label="Remover da cesta"
                  onClick={() => toggleSelect(item.id)}
                >
                  Remover
                </Button>
              </li>
            ))}
          </ul>

          <Button onClick={() => setShowCreateDialog(true)}>
            Criar encaminhamento ({selectedArray.length})
          </Button>

          {/* Similar OPEN reports panel */}
          <div className="mt-2 border-t border-gray-200 pt-3">
            <h4 className="text-sm font-semibold text-gray-700">Relatos similares abertos</h4>
            <p className="text-xs text-gray-400 italic">
              Relatos pendentes parecidos com a cesta (fora dela)
            </p>
            {similar.isLoading && (
              <div role="status" className="mt-2 text-xs text-gray-400">
                Buscando similares…
              </div>
            )}
            {similar.error &&
              (similar.error instanceof ApiError && similar.error.status === 503 ? (
                <div role="status" aria-live="polite" className="mt-2 text-sm text-gray-500">
                  Busca de similares indisponível.
                </div>
              ) : (
                <div role="alert" className="mt-2 text-sm text-red-500">
                  Erro ao buscar similares.
                </div>
              ))}
            {!similar.isLoading && !similar.error && similar.data && similar.data.length === 0 && (
              <div role="status" className="mt-2 text-xs text-gray-400">
                Nenhum relato similar aberto encontrado.
              </div>
            )}
            {similar.data && similar.data.length > 0 && (
              <ul className="mt-2 space-y-2">
                {similar.data.map((r) => (
                  <li
                    key={r.id}
                    className="flex items-start justify-between gap-2 rounded-md border border-gray-200 p-2 text-xs"
                  >
                    <div className="min-w-0">
                      <div className="text-gray-700 line-clamp-2">{r.text}</div>
                      <div className="text-gray-400 mt-1">
                        {urgencyLabel(r.urgency)} · score {r.score.toFixed(2)}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      aria-label="Adicionar à cesta"
                      onClick={() => toggleSelect(r.id)}
                    >
                      Adicionar
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}

      <CreateForwardingDialog
        open={showCreateDialog}
        selectedIds={selectedArray}
        onSuccess={clearSelection}
        onClose={() => setShowCreateDialog(false)}
      />
    </div>
  )
}
