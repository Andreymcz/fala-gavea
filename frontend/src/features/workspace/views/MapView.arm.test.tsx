import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

// ─── Mock react-leaflet so jsdom can render the map shell ────────────────────
// useMapEvents stores the latest click handlers so the test can simulate a
// map click, exercising the "Adicionar relato aqui" arm flow.
let lastClickHandlers: Array<(e: { latlng: { lat: number; lng: number } }) => void> = []

vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="map">{children}</div>,
  TileLayer: () => null,
  Marker: () => <div data-testid="provisional-marker" />,
  useMap: () => ({ getBounds: () => ({ getSouth: () => 0, getWest: () => 0, getNorth: () => 1, getEast: () => 1 }) }),
  useMapEvents: (handlers: { click?: (e: { latlng: { lat: number; lng: number } }) => void }) => {
    if (handlers.click) lastClickHandlers.push(handlers.click)
    return null
  },
}))

vi.mock('react-leaflet-cluster', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

vi.mock('@/features/map/ReportMarkers', () => ({ ReportMarkers: () => null }))

vi.mock('@/hooks/useFilteredReports', () => ({
  useFilteredReports: () => ({ features: [] }),
}))
vi.mock('@/hooks/useReportTypes', () => ({
  useReportTypes: () => ({ data: [] }),
}))

const mockSetBbox = vi.fn()
vi.mock('@/store/workspaceStore', () => ({
  useWorkspaceStore: (sel: (s: Record<string, unknown>) => unknown) =>
    sel({
      selectedIds: new Set<string>(),
      toggleSelect: vi.fn(),
      setBbox: mockSetBbox,
      filters: {},
    }),
}))

const mockNavigate = vi.fn()
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}))

let mockUser: { id: string; role: string } | null = { id: 'u-1', role: 'citizen' }
vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => ({ user: mockUser }),
}))

// Capture InlineReportDialog props instead of rendering the full dialog.
const dialogProps: Array<{ open: boolean; lat: number; lon: number }> = []
vi.mock('@/features/report/InlineReportDialog', () => ({
  InlineReportDialog: (props: { open: boolean; lat: number; lon: number }) => {
    dialogProps.push({ open: props.open, lat: props.lat, lon: props.lon })
    return <div data-testid="inline-dialog">dialog {props.lat},{props.lon}</div>
  },
}))

const mockToast = vi.fn()
vi.mock('@/components/ui/toast', () => ({ toast: (...args: unknown[]) => mockToast(...args) }))

import { MapView } from './MapView'

beforeEach(() => {
  lastClickHandlers = []
  dialogProps.length = 0
  mockNavigate.mockClear()
  mockToast.mockClear()
  mockUser = { id: 'u-1', role: 'citizen' }
})

describe('MapView — adicionar relato arm mode', () => {
  it('arming and clicking the map opens a prefilled inline dialog', async () => {
    render(<MapView />)

    const armBtn = screen.getByRole('button', { name: /adicionar relato clicando no mapa/i })
    fireEvent.click(armBtn)

    // Simulate the next map click (the AddReportHandler registers a click handler)
    expect(lastClickHandlers.length).toBeGreaterThan(0)
    lastClickHandlers.forEach((h) => h({ latlng: { lat: -22.95, lng: -43.2 } }))

    await waitFor(() => {
      expect(screen.getByTestId('inline-dialog')).toBeTruthy()
    })
    const opened = dialogProps.find((p) => p.open)
    expect(opened).toBeDefined()
    expect(opened?.lat).toBe(-22.95)
    expect(opened?.lon).toBe(-43.2)
  })

  it('anonymous users get a login prompt instead of arming', () => {
    mockUser = null
    render(<MapView />)
    fireEvent.click(screen.getByRole('button', { name: /adicionar relato clicando no mapa/i }))
    expect(mockNavigate).toHaveBeenCalledWith('/login')
    expect(mockToast).toHaveBeenCalled()
    // No dialog opened
    expect(dialogProps.find((p) => p.open)).toBeUndefined()
  })
})
