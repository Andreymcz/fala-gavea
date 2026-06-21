import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { api } from '@/lib/api'
import type { ReportFeature, ReportSearchResult, ReportQueryBody } from '@/lib/types'

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
  const { semanticQuery, urgency, status, type_id, since, until, bbox } = filters

  const semanticActive = Boolean(semanticQuery && semanticQuery.trim().length > 0)

  const body: ReportQueryBody = {
    limit: 200,
  }
  if (type_id) body.report_type_ids = [type_id]
  if (urgency) body.urgencies = [urgency]
  if (status) body.statuses = [status]
  if (since) body.since = since
  if (until) body.until = until
  if (bbox) body.bbox = bbox
  if (semanticActive) body.q = semanticQuery

  const { data, isLoading } = useQuery({
    queryKey: ['reports', 'query', body],
    queryFn: () => api.queryReports(body),
    staleTime: 30_000,
    placeholderData: keepPreviousData,
  })

  const features: ReportFeature[] = (data?.items ?? []).map((item) => ({
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [item.lon, item.lat] },
    properties: {
      id: item.id,
      text: item.text,
      urgency: item.urgency,
      status: item.status,
      report_type_id: item.report_type_id,
      author_id: item.author_id,
      photo_url: item.photo_url,
      created_at: item.created_at,
    },
  }))

  return {
    features,
    count: data?.total ?? 0,
    isLoading,
    semanticActive,
    semanticTruncated: false,
  }
}
