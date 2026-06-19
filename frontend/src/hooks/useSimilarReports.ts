import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useWorkspaceStore } from '@/store/workspaceStore'

export function useSimilarReports() {
  const similarSeedId = useWorkspaceStore((s) => s.similarSeedId)
  return useQuery({
    queryKey: ['similar', similarSeedId],
    queryFn: () => api.getSimilarReports(similarSeedId!, 5),
    enabled: !!similarSeedId,
    staleTime: 60_000,
    retry: false,
  })
}
