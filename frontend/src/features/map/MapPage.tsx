import { useState } from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { MapFilters } from "./FiltersSidebar";
import { FiltersSidebar } from "./FiltersSidebar";
import { ReportMarkers } from "./ReportMarkers";
import { useReports } from "@/hooks/useReports";
import { useReportTypes } from "@/hooks/useReportTypes";
import { useAuth } from "@/auth/AuthContext";
import type { ReportFilters } from "@/lib/types";

const GAVEA_CENTER: [number, number] = [-22.9731, -43.2272];
const DEFAULT_ZOOM = 15;

function filtersToApiFilters(f: MapFilters): ReportFilters {
  return {
    urgency: f.urgency || undefined,
    status: f.status || undefined,
    type_id: f.type_id,
    since: f.since,
    until: f.until,
  };
}

export function MapPage() {
  const { user } = useAuth();
  const isAgent = user?.role === "agent" || user?.role === "admin";

  const [mapFilters, setMapFilters] = useState<MapFilters>({});
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const apiFilters = filtersToApiFilters(mapFilters);
  const { data: geojson, isLoading } = useReports(apiFilters);
  const { data: reportTypes = [] } = useReportTypes();

  const typeMap = new Map(reportTypes.map((rt) => [rt.id, rt.name]));
  const features = geojson?.features ?? [];

  function toggleSelect(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  return (
    <div className="flex flex-1 overflow-hidden">
      <FiltersSidebar
        filters={mapFilters}
        onChange={(f) => {
          setMapFilters(f);
          setSelectedIds(new Set());
        }}
        reportTypes={reportTypes}
      />
      <div className="relative flex-1">
        {isLoading && (
          <div className="absolute inset-0 z-[500] flex items-center justify-center bg-white/60">
            <span className="text-gray-500 text-sm">Carregando relatos...</span>
          </div>
        )}
        {features.length === 0 && !isLoading && (
          <div className="absolute inset-0 z-[400] flex items-center justify-center pointer-events-none">
            <p className="rounded-md bg-white/90 px-4 py-2 text-sm text-gray-500 shadow">
              Nenhum relato registrado na Gávea ainda. Seja o primeiro!
            </p>
          </div>
        )}
        <MapContainer
          center={GAVEA_CENTER}
          zoom={DEFAULT_ZOOM}
          className="h-full w-full"
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <ReportMarkers
            features={features}
            typeMap={typeMap}
            isAgent={isAgent}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelect}
          />
        </MapContainer>

        {/* Wave-2 placeholder: chat affordance */}
        <div
          className="absolute bottom-4 left-4 z-[1000] opacity-50 cursor-not-allowed"
          title="Disponível em breve"
        >
          <div className="rounded-full bg-white border border-gray-300 px-3 py-1.5 text-xs text-gray-500 shadow">
            💬 Chat NL (em breve)
          </div>
        </div>
      </div>
    </div>
  );
}
