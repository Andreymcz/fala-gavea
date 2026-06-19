import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useWorkspaceStore } from '@/store/workspaceStore'
import type { TopicListResponse, ReportFilters } from '@/lib/types'

export function useTopics() {
  const filters = useWorkspaceStore((s) => s.filters)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { semanticQuery: _semanticQuery, ...structuredFilters } = filters // strip semanticQuery
  return useQuery<TopicListResponse, Error>({
    queryKey: ['topics', structuredFilters],
    queryFn: () => api.getTopics(structuredFilters as ReportFilters, 3),
    staleTime: 60_000,
    retry: false, // 503 should not retry
  })
}
