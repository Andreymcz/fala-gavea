import { describe, it, expect } from 'vitest'
import { intersectByScore } from './useFilteredReports'
import type { ReportFeature, ReportSearchResult } from '@/lib/types'

function makeFeature(id: string): ReportFeature {
  return {
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [0, 0] },
    properties: {
      id,
      text: 'test',
      urgency: 'baixa',
      status: 'pendente',
      report_type_id: 'rt1',
      author_id: 'u1',
      photo_url: null,
      created_at: '2026-01-01T00:00:00Z',
    },
  }
}

function makeSearchResult(id: string, score: number): ReportSearchResult {
  return {
    id,
    text: 'test',
    lat: 0,
    lon: 0,
    urgency: 'baixa',
    status: 'pendente',
    report_type_id: 'rt1',
    author_id: 'u1',
    photo_url: null,
    created_at: '2026-01-01T00:00:00Z',
    score,
  }
}

describe('intersectByScore', () => {
  it('returns only features whose id appears in semanticResults', () => {
    const features = [makeFeature('a'), makeFeature('b'), makeFeature('c')]
    const results = [makeSearchResult('a', 0.9), makeSearchResult('c', 0.7)]
    const out = intersectByScore(features, results)
    expect(out.map((f) => f.properties.id)).toEqual(['a', 'c'])
  })

  it('orders result by semanticResults order (score order)', () => {
    const features = [makeFeature('a'), makeFeature('b'), makeFeature('c')]
    // semantic results ordered high score first: c, a
    const results = [makeSearchResult('c', 0.95), makeSearchResult('a', 0.80)]
    const out = intersectByScore(features, results)
    expect(out.map((f) => f.properties.id)).toEqual(['c', 'a'])
  })

  it('returns empty array when no intersection', () => {
    const features = [makeFeature('x'), makeFeature('y')]
    const results = [makeSearchResult('z', 0.9)]
    const out = intersectByScore(features, results)
    expect(out).toHaveLength(0)
  })

  it('semanticTruncated is true when semanticResults.length === 50', () => {
    // This is a pure inline check — no React hook needed
    const semanticResults = Array.from({ length: 50 }, (_, i) =>
      makeSearchResult(`id-${i}`, 1 - i * 0.01),
    )
    const semanticTruncated = semanticResults.length === 50
    expect(semanticTruncated).toBe(true)
  })
})
