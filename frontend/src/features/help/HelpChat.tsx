import { useState } from 'react'
import { useAuth } from '@/auth/AuthContext'
import { postHelpChat, type CitedDoc } from '@/api/helpChat'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const ERROR_COPY: Record<string, string> = {
  unavailable: 'O assistente de ajuda está indisponível no momento. Tente novamente mais tarde.',
  rate_limit: 'Muitas perguntas em pouco tempo. Aguarde um instante e tente novamente.',
  unauthorized: 'Sua sessão expirou. Entre novamente para usar a Ajuda.',
  error: 'Não foi possível obter uma resposta. Tente novamente.',
}

interface Answer {
  response: string
  citedDocs: CitedDoc[]
}

export function HelpChat() {
  const { user, token } = useAuth()
  const [input, setInput] = useState('')
  const [isPending, setIsPending] = useState(false)
  const [answer, setAnswer] = useState<Answer | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Platform-helper chat is only available to authenticated users.
  if (!user || !token) return null

  async function handleSend() {
    const message = input.trim()
    if (!message || isPending || !token) return
    setIsPending(true)
    setError(null)
    setAnswer(null)
    try {
      const data = await postHelpChat(message, token)
      setAnswer({ response: data.response, citedDocs: data.cited_docs })
    } catch (err) {
      const key = err instanceof Error ? err.message : 'error'
      setError(ERROR_COPY[key] ?? ERROR_COPY.error)
    } finally {
      setIsPending(false)
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-gray-600">
        Tire dúvidas sobre como usar a plataforma Fala-Gávea. As respostas vêm da documentação do
        sistema.
      </p>

      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              void handleSend()
            }
          }}
          placeholder="Como faço para registrar um relato?"
          disabled={isPending}
          aria-label="Pergunta sobre a plataforma"
          className="flex-1 text-sm"
        />
        <Button onClick={() => void handleSend()} disabled={isPending || !input.trim()} size="sm">
          {isPending ? '...' : 'Perguntar'}
        </Button>
      </div>

      <div aria-live="polite" aria-atomic="true">
        {error && (
          <div role="status" className="rounded-md bg-amber-50 p-3 text-sm text-amber-800">
            {error}
          </div>
        )}

        {answer && (
          <div className="space-y-3">
            <div className="whitespace-pre-wrap rounded-md bg-gray-100 p-3 text-sm text-gray-800">
              {answer.response}
            </div>

            {answer.citedDocs.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Fontes
                </h4>
                <ul className="mt-1 space-y-1">
                  {answer.citedDocs.map((doc, i) => (
                    <li key={`${doc.source_path}#${doc.section_title}#${i}`} className="text-xs text-gray-500">
                      {doc.source_path}
                      {doc.section_title ? `#${doc.section_title}` : ''}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
