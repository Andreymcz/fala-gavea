export interface CitedDoc {
  source_path: string
  section_title: string
  score: number
}

export interface HelpChatResponse {
  response: string
  cited_docs: CitedDoc[]
}

export async function postHelpChat(message: string, token: string): Promise<HelpChatResponse> {
  const res = await fetch('/nl/help', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ message }),
  })
  if (res.status === 401) throw new Error('unauthorized')
  if (res.status === 429) throw new Error('rate_limit')
  if (res.status === 503) throw new Error('unavailable')
  if (!res.ok) throw new Error('error')
  return res.json() as Promise<HelpChatResponse>
}
