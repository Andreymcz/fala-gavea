import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { ReportSearchResult } from '@/lib/types'

export function useSemanticSearch(q: string) {
  const { data, isLoading } = useQuery<ReportSearchResult[]>({
    queryKey: ['reports', 'search', q],
    queryFn: () => api.searchReports(q, 50),
    enabled: q.trim().length > 0,
    staleTime: 30_000,
    placeholderData: keepPreviousData,
  })
  return { data, isLoading }
}
