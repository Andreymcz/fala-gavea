import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, useMap, useMapEvents } from 'react-leaflet'
import MarkerClusterGroup from 'react-leaflet-cluster'
import 'leaflet/dist/leaflet.css'
import type { LatLng, LatLngBounds } from 'leaflet'
import { ReportMarkers } from '@/features/map/ReportMarkers'
import { InlineReportDialog } from '@/features/report/InlineReportDialog'
import { useFilteredReports } from '@/hooks/useFilteredReports'
import { useReportTypes } from '@/hooks/useReportTypes'
import { useAuth } from '@/auth/AuthContext'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { toast } from '@/components/ui/toast'

const GAVEA_CENTER: [number, number] = [-22.9731, -43.2272]
const DEFAULT_ZOOM = 15

// ────────────────────────────────────────────────────────────
// BboxDrawHandler — internal component that lives inside the
// MapContainer so it can use useMapEvents.
// ────────────────────────────────────────────────────────────
interface BboxDrawHandlerProps {
  drawing: boolean
  onBboxCommit: (bbox: string) => void
  onDrawEnd: () => void
}

function BboxDrawHandler({ drawing, onBboxCommit, onDrawEnd }: BboxDrawHandlerProps) {
  const [corner1, setCorner1] = useState<LatLng | null>(null)

  useMapEvents({
    click(e) {
      if (!drawing) return
      if (corner1 === null) {
        setCorner1(e.latlng)
      } else {
        const minLat = Math.min(corner1.lat, e.latlng.lat)
        const minLon = Math.min(corner1.lng, e.latlng.lng)
        const maxLat = Math.max(corner1.lat, e.latlng.lat)
        const maxLon = Math.max(corner1.lng, e.latlng.lng)
        onBboxCommit(`${minLat},${minLon},${maxLat},${maxLon}`)
        setCorner1(null)
        onDrawEnd()
      }
    },
  })

  return null
}

// ────────────────────────────────────────────────────────────
// AddReportHandler — captures the next map click while the
// "Adicionar relato aqui" mode is armed.
// ────────────────────────────────────────────────────────────
interface AddReportHandlerProps {
  arming: boolean
  onPick: (latlng: LatLng) => void
}

function AddReportHandler({ arming, onPick }: AddReportHandlerProps) {
  useMapEvents({
    click(e) {
      if (!arming) return
      onPick(e.latlng)
    },
  })
  return null
}

// ────────────────────────────────────────────────────────────
// MapControls — overlay buttons inside MapContainer so they
// can call useMap() to read current viewport bounds.
// ────────────────────────────────────────────────────────────
interface MapControlsProps {
  onFilterArea: (bounds: LatLngBounds) => void
  onClearArea: () => void
  hasBbox: boolean
}

function MapControls({ onFilterArea, onClearArea, hasBbox }: MapControlsProps) {
  const map = useMap()

  return (
    <div
      className="absolute top-2 left-1/2 -translate-x-1/2 z-[1000] flex gap-2"
      style={{ zIndex: 1000 }}
    >
      <button
        type="button"
        onClick={() => onFilterArea(map.getBounds())}
        aria-label="Filtrar relatórios na área visível do mapa"
        className={[
          'min-h-[44px] px-4 py-2 rounded-md text-sm font-medium shadow-md',
          'bg-blue-600 text-white border border-blue-700',
          'hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500',
        ].join(' ')}
      >
        Filtrar nesta área
      </button>
      <button
        type="button"
        onClick={onClearArea}
        disabled={!hasBbox}
        aria-label="Limpar filtro de área do mapa"
        className={[
          'min-h-[44px] px-3 py-2 rounded-md text-sm font-medium shadow-md',
          'bg-white border border-red-300 text-red-600',
          'hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500',
          'disabled:opacity-40 disabled:cursor-not-allowed',
        ].join(' ')}
      >
        Limpar área
      </button>
    </div>
  )
}

// ────────────────────────────────────────────────────────────
// MapView — the public widget component
// ────────────────────────────────────────────────────────────
export function MapView() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const isAgent = user?.role === 'agent' || user?.role === 'admin'

  const { features } = useFilteredReports()
  const { data: reportTypes = [] } = useReportTypes()
  const typeMap = new Map(reportTypes.map((rt) => [rt.id, rt.name]))

  const selectedIds = useWorkspaceStore((s) => s.selectedIds)
  const toggleSelect = useWorkspaceStore((s) => s.toggleSelect)
  const setBbox = useWorkspaceStore((s) => s.setBbox)
  const currentBbox = useWorkspaceStore((s) => s.filters.bbox)

  const [drawing, setDrawing] = useState(false)
  const [addingReport, setAddingReport] = useState(false)
  const [pickedPoint, setPickedPoint] = useState<{ lat: number; lon: number } | null>(null)

  const handleDrawStart = useCallback(() => {
    // Arm modes are mutually exclusive: drawing disarms add-report.
    setAddingReport(false)
    setDrawing(true)
  }, [])

  const handleClear = useCallback(() => {
    setBbox(undefined)
    setDrawing(false)
  }, [setBbox])

  const handleBboxCommit = useCallback(
    (bbox: string) => {
      setBbox(bbox)
    },
    [setBbox],
  )

  const handleDrawEnd = useCallback(() => {
    setDrawing(false)
  }, [])

  const handleFilterArea = useCallback(
    (bounds: LatLngBounds) => {
      setBbox(
        `${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()}`,
      )
    },
    [setBbox],
  )

  const handleAddReportArm = useCallback(() => {
    if (!user) {
      toast('Faça login para adicionar um relato.', 'info')
      navigate('/login')
      return
    }
    // Arm modes are mutually exclusive: add-report disarms bbox draw.
    setDrawing(false)
    setAddingReport(true)
  }, [user, navigate])

  const handleAddReportCancel = useCallback(() => {
    setAddingReport(false)
  }, [])

  const handlePickPoint = useCallback((latlng: LatLng) => {
    setPickedPoint({ lat: latlng.lat, lon: latlng.lng })
    setAddingReport(false)
  }, [])

  const handleDialogChange = useCallback((open: boolean) => {
    if (!open) setPickedPoint(null)
  }, [])

  return (
    <div className="relative flex-1 h-full min-h-[300px] min-w-[300px]">
      {/* Bbox + add-report controls overlay */}
      <div
        className="absolute top-2 right-2 z-[1000] flex gap-2"
        style={{ zIndex: 1000 }}
      >
        <button
          type="button"
          onClick={handleDrawStart}
          disabled={drawing}
          aria-pressed={drawing}
          aria-label="Desenhar área de filtro no mapa"
          className={[
            'min-h-[44px] px-3 py-2 rounded-md text-sm font-medium shadow',
            'bg-white border border-gray-300 text-gray-700',
            'hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'disabled:opacity-60 disabled:cursor-not-allowed',
          ].join(' ')}
        >
          {drawing ? 'Clique 2x no mapa…' : 'Desenhar área'}
        </button>
        {addingReport ? (
          <button
            type="button"
            onClick={handleAddReportCancel}
            aria-pressed={true}
            aria-label="Cancelar adição de relato"
            className={[
              'min-h-[44px] px-3 py-2 rounded-md text-sm font-medium shadow',
              'bg-green-600 text-white border border-green-700',
              'hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500',
            ].join(' ')}
          >
            Clique no mapa… (cancelar)
          </button>
        ) : (
          <button
            type="button"
            onClick={handleAddReportArm}
            aria-pressed={false}
            aria-label="Adicionar relato clicando no mapa"
            className={[
              'min-h-[44px] px-3 py-2 rounded-md text-sm font-medium shadow',
              'bg-white border border-green-400 text-green-700',
              'hover:bg-green-50 focus:outline-none focus:ring-2 focus:ring-green-500',
            ].join(' ')}
          >
            Adicionar relato aqui
          </button>
        )}
        {currentBbox && (
          <button
            type="button"
            onClick={handleClear}
            aria-label="Limpar área de filtro"
            className={[
              'min-h-[44px] px-3 py-2 rounded-md text-sm font-medium shadow',
              'bg-white border border-red-300 text-red-600',
              'hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500',
            ].join(' ')}
          >
            Limpar área
          </button>
        )}
      </div>

      <MapContainer
        center={GAVEA_CENTER}
        zoom={DEFAULT_ZOOM}
        className="h-full w-full"
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <BboxDrawHandler
          drawing={drawing}
          onBboxCommit={handleBboxCommit}
          onDrawEnd={handleDrawEnd}
        />
        <AddReportHandler arming={addingReport} onPick={handlePickPoint} />
        <MapControls
          onFilterArea={handleFilterArea}
          onClearArea={handleClear}
          hasBbox={!!currentBbox}
        />
        {pickedPoint && (
          <Marker position={[pickedPoint.lat, pickedPoint.lon]} />
        )}
        <MarkerClusterGroup>
          <ReportMarkers
            features={features}
            typeMap={typeMap}
            isAgent={isAgent}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelect}
          />
        </MarkerClusterGroup>
      </MapContainer>

      {pickedPoint && (
        <InlineReportDialog
          key={`${pickedPoint.lat},${pickedPoint.lon}`}
          open={true}
          lat={pickedPoint.lat}
          lon={pickedPoint.lon}
          onOpenChange={handleDialogChange}
        />
      )}
    </div>
  )
}
