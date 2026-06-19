import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { ChatRequest, ChatResponse } from '@/lib/types'

export function useChat() {
  return useMutation<ChatResponse, Error, ChatRequest>({
    mutationFn: (body) => api.chat(body),
  })
}
