import { useRef } from 'react'
import { useAuth } from '@/auth/AuthContext'
import { useWorkspaceStore, type ViewId } from '@/store/workspaceStore'

interface ViewMeta {
  id: ViewId
  label: string
  description: string
  agentOnly?: boolean
}

const VIEW_META: ViewMeta[] = [
  { id: 'map', label: 'Mapa', description: 'Veja os relatos no mapa da Gávea' },
  { id: 'table', label: 'Tabela', description: 'Liste e selecione relatos para encaminhar' },
  { id: 'topics', label: 'Tópicos', description: 'Temas emergentes no subconjunto filtrado (IA)', agentOnly: true },
  { id: 'similars', label: 'Similares', description: 'Relatos parecidos com um relato-semente' },
  { id: 'chat', label: 'Chat', description: 'Pergunte sobre os relatos em linguagem natural (IA)', agentOnly: true },
]

export function ViewToggleBar() {
  const { user } = useAuth()
  const { activeViews, toggleView } = useWorkspaceStore()
  const barRef = useRef<HTMLDivElement>(null)

  const isAgentOrAdmin = user?.role === 'agent' || user?.role === 'admin'

  function handleToggle(id: ViewId) {
    const wasActive = activeViews.includes(id)
    toggleView(id)
    if (wasActive) {
      // View was removed — return focus to the bar
      requestAnimationFrame(() => {
        barRef.current?.focus()
      })
    }
  }

  const visibleViews = VIEW_META.filter((v) => !v.agentOnly || isAgentOrAdmin)

  return (
    <div
      ref={barRef}
      className="flex items-center gap-2 px-3 py-2 border-b border-gray-200 bg-white flex-wrap"
      tabIndex={-1}
      aria-label="Visões do workspace"
    >
      {visibleViews.map((meta) => {
        const active = activeViews.includes(meta.id)
        return (
          <button
            key={meta.id}
            type="button"
            aria-pressed={active}
            aria-label={`${meta.label}: ${meta.description}`}
            onClick={() => handleToggle(meta.id)}
            className={[
              'flex flex-col items-start px-3 py-1.5 rounded-md border text-left transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500',
              active
                ? 'bg-blue-600 border-blue-600 text-white'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50',
            ].join(' ')}
          >
            <span className="text-xs font-semibold leading-none">{meta.label}</span>
            <span className={`text-[10px] leading-tight mt-0.5 ${active ? 'text-blue-100' : 'text-gray-400'}`}>
              {meta.description}
            </span>
          </button>
        )
      })}
    </div>
  )
}
