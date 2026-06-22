import { useQuery } from '@tanstack/react-query'
import { api, ApiError } from '@/lib/api'
import type { ReportSearchResult } from '@/lib/types'

/**
 * Client-side fan-out fallback used when the centroid endpoint
 * (POST /reports/similar-to-set) is unavailable (503).
 *
 * Calls GET /reports/{id}/similar for each seed, unions + dedupes the
 * neighborhoods, excludes the seed ids, and keeps only `pendente` reports
 * (Decision D-010: "open" == pendente).
 */
async function fanOutSimilar(reportIds: string[], n: number): Promise<ReportSearchResult[]> {
  const seeds = new Set(reportIds)
  const results = await Promise.all(
    reportIds.map((id) => api.getSimilarReports(id, n).catch(() => [] as ReportSearchResult[])),
  )

  const byId = new Map<string, ReportSearchResult>()
  for (const neighbors of results) {
    for (const r of neighbors) {
      if (seeds.has(r.id)) continue
      if (r.status !== 'pendente') continue
      const existing = byId.get(r.id)
      // keep the highest score seen across neighborhoods
      if (!existing || r.score > existing.score) {
        byId.set(r.id, r)
      }
    }
  }

  return Array.from(byId.values())
    .sort((a, b) => b.score - a.score)
    .slice(0, n)
}

export function useSimilarToSet(reportIds: string[], n = 10) {
  const sortedKey = [...reportIds].sort()
  return useQuery({
    queryKey: ['similar-to-set', sortedKey, n],
    enabled: reportIds.length > 0,
    staleTime: 60_000,
    retry: false,
    queryFn: async () => {
      try {
        return await api.similarToSet(reportIds, n)
      } catch (err) {
        if (err instanceof ApiError && (err.status === 503 || err.status === 404)) {
          return fanOutSimilar(reportIds, n)
        }
        throw err
      }
    },
  })
}
