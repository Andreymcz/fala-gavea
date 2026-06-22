import { useState } from "react";
import type { Urgency, CreateReportBody } from "@/lib/types";

export interface ReportFormErrors {
  text?: string;
  lat?: string;
  lon?: string;
  report_type_id?: string;
  urgency?: string;
}

export interface UseReportFormOptions {
  /** Prefill latitude (decimal string). */
  initialLat?: string;
  /** Prefill longitude (decimal string). */
  initialLon?: string;
}

export interface UseReportFormResult {
  text: string;
  setText: (v: string) => void;
  lat: string;
  setLat: (v: string) => void;
  lon: string;
  setLon: (v: string) => void;
  urgency: Urgency | "";
  setUrgency: (v: Urgency | "") => void;
  reportTypeId: string;
  setReportTypeId: (v: string) => void;
  photoUrl: string;
  setPhotoUrl: (v: string) => void;
  geoError: string | null;
  geoLoading: boolean;
  errors: ReportFormErrors;
  handleGeolocate: () => void;
  validate: () => boolean;
  /** Returns the request body when valid, otherwise null (and sets errors). */
  buildBody: () => CreateReportBody | null;
}

/**
 * Shared report form state + validation, reused by the standalone /report page
 * and the inline map-click create dialog.
 */
export function useReportForm(options: UseReportFormOptions = {}): UseReportFormResult {
  const [text, setText] = useState("");
  const [lat, setLat] = useState(options.initialLat ?? "");
  const [lon, setLon] = useState(options.initialLon ?? "");
  const [urgency, setUrgency] = useState<Urgency | "">("");
  const [reportTypeId, setReportTypeId] = useState("");
  const [photoUrl, setPhotoUrl] = useState("");
  const [geoError, setGeoError] = useState<string | null>(null);
  const [geoLoading, setGeoLoading] = useState(false);
  const [errors, setErrors] = useState<ReportFormErrors>({});

  function validate(): boolean {
    const errs: ReportFormErrors = {};
    if (text.trim().length < 10)
      errs.text = "Descrição deve ter pelo menos 10 caracteres.";
    if (text.trim().length > 2000)
      errs.text = "Descrição deve ter no máximo 2000 caracteres.";
    const latNum = parseFloat(lat);
    const lonNum = parseFloat(lon);
    if (!lat || isNaN(latNum) || latNum < -90 || latNum > 90)
      errs.lat = "Latitude inválida (deve ser entre -90 e 90).";
    if (!lon || isNaN(lonNum) || lonNum < -180 || lonNum > 180)
      errs.lon = "Longitude inválida (deve ser entre -180 e 180).";
    if (!reportTypeId) errs.report_type_id = "Selecione o tipo de problema.";
    if (!urgency) errs.urgency = "Selecione a urgência.";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  function buildBody(): CreateReportBody | null {
    if (!validate()) return null;
    return {
      text: text.trim(),
      lat: parseFloat(lat),
      lon: parseFloat(lon),
      urgency: urgency as Urgency,
      report_type_id: reportTypeId,
      photo_url: photoUrl.trim() || undefined,
    };
  }

  function handleGeolocate() {
    if (!navigator.geolocation) {
      setGeoError("Geolocalização não disponível. Preencha latitude e longitude manualmente.");
      return;
    }
    setGeoLoading(true);
    setGeoError(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLat(pos.coords.latitude.toFixed(6));
        setLon(pos.coords.longitude.toFixed(6));
        setGeoLoading(false);
      },
      () => {
        setGeoError("Geolocalização não disponível. Preencha latitude e longitude manualmente.");
        setGeoLoading(false);
      },
    );
  }

  return {
    text,
    setText,
    lat,
    setLat,
    lon,
    setLon,
    urgency,
    setUrgency,
    reportTypeId,
    setReportTypeId,
    photoUrl,
    setPhotoUrl,
    geoError,
    geoLoading,
    errors,
    handleGeolocate,
    validate,
    buildBody,
  };
}
