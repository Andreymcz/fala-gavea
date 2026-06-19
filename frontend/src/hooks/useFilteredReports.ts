import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { api } from '@/lib/api'
import { useSemanticSearch } from './useSemanticSearch'
import type { ReportFeature, ReportSearchResult, ReportGeoJSON } from '@/lib/types'

export function intersectByScore(
  features: ReportFeature[],
  semanticResults: ReportSearchResult[],
): ReportFeature[] {
  const featureMap = new Map(features.map((f) => [f.properties.id, f]))
  const result: ReportFeature[] = []
  for (const sr of semanticResults) {
    const feature = featureMap.get(sr.id)
    if (feature) {
      result.push(feature)
    }
  }
  return result
}

export function useFilteredReports() {
  const filters = useWorkspaceStore((s) => s.filters)
  const { semanticQuery, ...structuredFilters } = filters

  const geoQuery = useQuery<ReportGeoJSON>({
    queryKey: ['reports', structuredFilters],
    queryFn: () => api.getReportsGeoJSON(structuredFilters),
    staleTime: 30_000,
    placeholderData: keepPreviousData,
  })

  const semanticActive = Boolean(semanticQuery && semanticQuery.trim().length > 0)
  const semanticSearch = useSemanticSearch(semanticQuery ?? '')

  const geoFeatures = geoQuery.data?.features ?? []
  const semanticResults = semanticSearch.data ?? []

  let features: ReportFeature[]
  if (semanticActive) {
    features = intersectByScore(geoFeatures, semanticResults)
  } else {
    features = geoFeatures
  }

  const isLoading =
    geoQuery.isLoading || (semanticActive && semanticSearch.isLoading)

  const semanticTruncated = semanticActive && semanticResults.length === 50

  return {
    features,
    count: features.length,
    isLoading,
    semanticActive,
    semanticTruncated,
  }
}
