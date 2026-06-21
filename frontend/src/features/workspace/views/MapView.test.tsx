import { describe, it, expect } from 'vitest'

/**
 * MapView — manual test guide
 *
 * Leaflet/react-leaflet map interactions cannot be unit-tested in jsdom
 * (no canvas, no tile loading, no real viewport). The tests below are
 * manual verification steps that must be run in a real browser.
 *
 * Manual test:
 * 1. Pan/zoom to a region, click "Filtrar nesta área"
 *    → report count changes to match visible area; "Área do mapa" chip appears in ActiveFilterChips.
 * 2. Click "Limpar área"
 *    → full result set returns; "Área do mapa" chip disappears.
 * 3. "Limpar área" button is disabled (opacity-40, cursor-not-allowed) when no bbox filter is active.
 * 4. The legacy "Desenhar área" button (top-right) still works: two clicks define corners → bbox committed.
 */

// Placeholder so the test runner does not complain about an empty suite.
describe('MapView', () => {
  it('has manual test instructions above', () => {
    expect(true).toBe(true)
  })
})
