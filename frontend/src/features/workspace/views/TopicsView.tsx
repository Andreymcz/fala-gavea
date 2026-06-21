import { ApiError } from '@/lib/api'
import { useKeywords } from '@/hooks/useKeywords'
import { useAuth } from '@/auth/AuthContext'

export function TopicsView() {
  const { user } = useAuth()
  const { data, isLoading, error } = useKeywords()

  const isAgent = user?.role === 'agent' || user?.role === 'admin'
  if (!isAgent) return null

  if (isLoading)
    return (
      <div role="status" className="p-4 text-sm text-gray-500">
        Carregando palavras-chave...
      </div>
    )

  if (error) {
    if (error instanceof ApiError && error.status === 503) {
      return (
        <div role="status" aria-live="polite" className="p-4 text-sm text-gray-500">
          Extração de palavras-chave indisponível.
        </div>
      )
    }
    return (
      <div role="alert" className="p-4 text-sm text-red-500">
        Erro ao carregar palavras-chave.
      </div>
    )
  }

  if (!data || data.keywords.length === 0) {
    return (
      <div role="status" className="p-4 text-sm text-gray-400">
        Nenhuma palavra-chave encontrada no subconjunto atual.
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3 p-4 overflow-auto">
      <h3 className="text-sm font-semibold text-gray-700">
        Palavras-chave — {data.total_reports} relatos
      </h3>
      <ul className="space-y-2">
        {data.keywords.map((t) => (
          <li key={t.cluster_id} className="rounded-md border border-gray-200 p-2">
            <div className="text-xs font-medium text-gray-600">
              {t.terms.slice(0, 5).join(', ')}
            </div>
            <div className="text-xs text-gray-400">
              {t.count} relato{t.count !== 1 ? 's' : ''}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
