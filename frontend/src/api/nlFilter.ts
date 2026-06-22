import type { WorkspaceFilters } from '@/lib/types'

export interface NLFilterResponse {
  body: Partial<WorkspaceFilters>
  warnings: string[]
}

export async function postNLFilter(text: string, token: string): Promise<NLFilterResponse> {
  const res = await fetch('/nl/filter', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ text }),
  })
  if (res.status === 429) throw new Error('rate_limit')
  if (res.status === 503) throw new Error('unavailable')
  if (!res.ok) throw new Error('error')
  return res.json() as Promise<NLFilterResponse>
}
