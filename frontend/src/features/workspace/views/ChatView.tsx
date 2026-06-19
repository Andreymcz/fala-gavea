import { useState, useRef, useEffect } from 'react'
import { useAuth } from '@/auth/AuthContext'
import { useChat } from '@/hooks/useChat'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { ApiError } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface Message {
  role: 'user' | 'assistant'
  text: string
  cited?: string[]
}

export function ChatView() {
  const { user } = useAuth()
  const { mutate: sendChat, isPending } = useChat()
  const setSimilarSeed = useWorkspaceStore((s) => s.setSimilarSeed)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [error503, setError503] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const isAgent = user?.role === 'agent' || user?.role === 'admin'
  if (!isAgent) return null

  function handleSend() {
    const text = input.trim()
    if (!text || isPending) return
    setInput('')
    setError503(false)
    setMessages((prev) => [...prev, { role: 'user', text }])
    sendChat(
      { message: text },
      {
        onSuccess: (data) => {
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', text: data.response, cited: data.cited_report_ids },
          ])
        },
        onError: (err) => {
          if (err instanceof ApiError && err.status === 503) {
            setError503(true)
          }
        },
      },
    )
  }

  return (
    <div className="flex flex-col h-full min-h-[300px]">
      <h3 className="text-sm font-semibold text-gray-700 p-3 border-b">Chat</h3>
      <div
        className="flex-1 overflow-auto p-3 space-y-3"
        aria-live="polite"
        aria-label="Conversa"
      >
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>
            <div
              className={`inline-block rounded-lg px-3 py-2 text-sm max-w-xs ${
                m.role === 'user' ? 'bg-blue-100 text-blue-900' : 'bg-gray-100 text-gray-800'
              }`}
            >
              {m.text}
              {m.cited && m.cited.length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1">
                  {m.cited.map((id) => (
                    <button
                      key={id}
                      onClick={() => setSimilarSeed(id)}
                      className="text-xs underline text-blue-600 hover:text-blue-800 focus:outline focus:outline-2 rounded px-1"
                    >
                      #{id.slice(0, 8)}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {error503 && (
          <div role="status" aria-live="polite" className="text-sm text-gray-500">
            Assistente indisponível.
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="flex gap-2 p-3 border-t">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          placeholder="Pergunte sobre os relatos..."
          disabled={isPending}
          className="flex-1 text-sm"
        />
        <Button onClick={handleSend} disabled={isPending || !input.trim()} size="sm">
          {isPending ? '...' : 'Enviar'}
        </Button>
      </div>
    </div>
  )
}
