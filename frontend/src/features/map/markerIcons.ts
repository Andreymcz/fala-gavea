import L from "leaflet";
import type { Urgency } from "@/lib/types";

const urgencyColors: Record<Urgency, string> = {
  alta: "#E53E3E",
  media: "#DD6B20",
  baixa: "#3182CE",
};

export const SEARCH_COLOR = "#805AD5";

export function createUrgencyIcon(urgency: Urgency): L.DivIcon {
  const color = urgencyColors[urgency];
  return L.divIcon({
    className: "",
    html: `<div style="
      width: 16px; height: 16px; border-radius: 50%;
      background: ${color}; border: 2px solid white;
      box-shadow: 0 1px 3px rgba(0,0,0,0.4);
    "></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

export function urgencyColor(urgency: Urgency): string {
  return urgencyColors[urgency];
}
