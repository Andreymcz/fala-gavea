import { Marker, Popup } from "react-leaflet";
import type { ReportFeature } from "@/lib/types";
import { createUrgencyIcon } from "./markerIcons";
import { ReportPopup } from "./ReportPopup";

interface ReportMarkersProps {
  features: ReportFeature[];
  typeMap: Map<string, string>;
  isAgent?: boolean;
  selectedIds?: Set<string>;
  onToggleSelect?: (id: string) => void;
}

export function ReportMarkers({
  features,
  typeMap,
  isAgent = false,
  selectedIds = new Set(),
  onToggleSelect,
}: ReportMarkersProps) {
  return (
    <>
      {features.map((feature) => {
        const [lon, lat] = feature.geometry.coordinates;
        const { id, urgency } = feature.properties;
        return (
          <Marker
            key={id}
            position={[lat, lon]}
            icon={createUrgencyIcon(urgency)}
            title={`${feature.properties.text.slice(0, 60)}...`}
          >
            <Popup>
              <ReportPopup
                feature={feature}
                typeMap={typeMap}
                isAgent={isAgent}
                isSelected={selectedIds.has(id)}
                onToggleSelect={onToggleSelect}
              />
            </Popup>
          </Marker>
        );
      })}
    </>
  );
}
