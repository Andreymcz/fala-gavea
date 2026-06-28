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
  addingReport: boolean
  onAddReportArm: () => void
  onAddReportCancel: () => void
}

function MapControls({ onFilterArea, addingReport, onAddReportArm, onAddReportCancel }: MapControlsProps) {
  const map = useMap()

  return (
    <div
      className="absolute top-2 right-2 z-[1000] flex flex-col gap-2"
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
      {addingReport ? (
        <button
          type="button"
          onClick={onAddReportCancel}
          aria-pressed={true}
          aria-label="Cancelar adição de relato"
          className={[
            'min-h-[44px] px-3 py-2 rounded-md text-sm font-medium shadow-md',
            'bg-green-600 text-white border border-green-700',
            'hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500',
          ].join(' ')}
        >
          Clique no mapa… (cancelar)
        </button>
      ) : (
        <button
          type="button"
          onClick={onAddReportArm}
          aria-pressed={false}
          aria-label="Adicionar relato clicando no mapa"
          className={[
            'min-h-[44px] px-3 py-2 rounded-md text-sm font-medium shadow-md',
            'bg-white border border-green-400 text-green-700',
            'hover:bg-green-50 focus:outline-none focus:ring-2 focus:ring-green-500',
          ].join(' ')}
        >
          Adicionar relato aqui
        </button>
      )}
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

  // allPoints: plot every matching relato (via /reports/geojson), not just the
  // first 200 page of /reports/query. Clustering handles the marker volume.
  const { features } = useFilteredReports({ allPoints: true })
  const { data: reportTypes = [] } = useReportTypes()
  const typeMap = new Map(reportTypes.map((rt) => [rt.id, rt.name]))

  const selectedIds = useWorkspaceStore((s) => s.selectedIds)
  const toggleSelect = useWorkspaceStore((s) => s.toggleSelect)
  const setBbox = useWorkspaceStore((s) => s.setBbox)

  const [addingReport, setAddingReport] = useState(false)
  const [pickedPoint, setPickedPoint] = useState<{ lat: number; lon: number } | null>(null)

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
    <div className="relative z-0 flex-1 h-full min-h-[300px] min-w-[300px]">
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
        <AddReportHandler arming={addingReport} onPick={handlePickPoint} />
        <MapControls
          onFilterArea={handleFilterArea}
          addingReport={addingReport}
          onAddReportArm={handleAddReportArm}
          onAddReportCancel={handleAddReportCancel}
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
