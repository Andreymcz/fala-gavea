import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { api } from '@/lib/api'
import type { ReportFeature, ReportSearchResult, ReportQueryBody, ReportDetail } from '@/lib/types'

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

/** Sentinel value used in author_id to indicate anonymous "Meus relatos" mode. */
export const ANON_AUTHOR_SENTINEL = '__anon__'

function reportsToFeatures(reports: ReportDetail[]): ReportFeature[] {
  return reports.map((r) => ({
    type: 'Feature' as const,
    geometry: { type: 'Point' as const, coordinates: [r.lon, r.lat] as [number, number] },
    properties: {
      id: r.id,
      text: r.text,
      urgency: r.urgency,
      status: r.status,
      report_type_id: r.report_type_id,
      author_id: r.author_id,
      photo_url: r.photo_url,
      created_at: r.created_at,
      score: null,
    },
  }))
}

export interface UseFilteredReportsOptions {
  limit?: number
  offset?: number
}

export function useFilteredReports(options?: UseFilteredReportsOptions) {
  const filters = useWorkspaceStore((s) => s.filters)
  const { semanticQuery, urgency, status, type_id, author_id, since, until, bbox } = filters

  const isAnonMode = author_id === ANON_AUTHOR_SENTINEL
  const anonToken = isAnonMode ? localStorage.getItem('fala_gavea_anon_token') : null

  const semanticActive = Boolean(semanticQuery && semanticQuery.trim().length > 0)

  // Anonymous "Meus relatos" query
  const anonQuery = useQuery({
    queryKey: ['reports', 'mine-anon', anonToken],
    queryFn: () => api.getMyAnonymousReports(anonToken!),
    staleTime: 30_000,
    enabled: isAnonMode && !!anonToken,
    placeholderData: keepPreviousData,
  })

  const body: ReportQueryBody = {
    limit: options?.limit ?? 200,
  }
  if (options?.offset != null) body.offset = options.offset
  if (type_id) body.report_type_ids = [type_id]
  if (urgency) body.urgencies = [urgency]
  if (status) body.statuses = [status]
  if (!isAnonMode && author_id) body.author_id = author_id
  if (since) body.since = since
  if (until) body.until = until
  if (bbox) body.bbox = bbox
  if (semanticActive) body.q = semanticQuery

  const { data, isLoading: normalLoading } = useQuery({
    queryKey: ['reports', 'query', body],
    queryFn: () => api.queryReports(body),
    staleTime: 30_000,
    placeholderData: keepPreviousData,
    enabled: !isAnonMode,
  })

  if (isAnonMode) {
    const anonFeatures = reportsToFeatures(anonQuery.data ?? [])
    return {
      features: anonFeatures,
      count: anonFeatures.length,
      total: anonFeatures.length,
      ranked_by: null,
      isLoading: anonQuery.isLoading,
      semanticActive: false,
      semanticTruncated: false,
    }
  }

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
      score: item.score,
    },
  }))

  return {
    features,
    count: data?.total ?? 0,
    total: data?.total ?? 0,
    ranked_by: data?.ranked_by ?? null,
    isLoading: normalLoading,
    semanticActive,
    semanticTruncated: false,
  }
}
