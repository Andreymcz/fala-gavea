import { ApiError } from '@/lib/api'
import { useSimilarReports } from '@/hooks/useSimilarReports'
import { useWorkspaceStore } from '@/store/workspaceStore'

function urgencyLabel(u: string) {
  if (u === 'alta') return '▲ Alta'
  if (u === 'media') return '● Média'
  return '▼ Baixa'
}

export function SimilarsView() {
  const similarSeedId = useWorkspaceStore((s) => s.similarSeedId)
  const { data, isLoading, error } = useSimilarReports()

  return (
    <div className="flex flex-col gap-2 p-4 overflow-auto">
      <h3 className="text-sm font-semibold text-gray-700">Similares</h3>
      <p className="text-xs text-gray-400 italic">Similares em toda a base, fora do filtro</p>
      {!similarSeedId && (
        <div role="status" className="text-xs text-gray-400">
          Clique em &quot;Ver similares&quot; em um relato para explorar relatos parecidos.
        </div>
      )}
      {similarSeedId && isLoading && (
        <div role="status" className="text-xs text-gray-400">
          Buscando similares...
        </div>
      )}
      {similarSeedId && error && (
        error instanceof ApiError && error.status === 503 ? (
          <div role="status" aria-live="polite" className="text-sm text-gray-500">
            Busca de similares indisponível.
          </div>
        ) : (
          <div role="alert" className="text-sm text-red-500">
            Erro ao buscar similares.
          </div>
        )
      )}
      {similarSeedId && data && data.length === 0 && (
        <div role="status" className="text-xs text-gray-400">
          Nenhum relato similar encontrado.
        </div>
      )}
      {similarSeedId && data && data.length > 0 && (
        <ul className="space-y-2">
          {data.map((r) => (
            <li key={r.id} className="rounded-md border border-gray-200 p-2 text-xs">
              <div className="text-gray-700 line-clamp-2">{r.text}</div>
              <div className="text-gray-400 mt-1">
                {urgencyLabel(r.urgency)} · {new Date(r.created_at).toLocaleDateString('pt-BR')}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
