export type UserRole = "citizen" | "agent" | "admin";
export type Urgency = "alta" | "media" | "baixa";
export type ReportStatus = "pendente" | "em_analise" | "encaminhado" | "resolvido";
export type ForwardingStatus = "aguardando_solucao" | "solucao_em_andamento" | "finalizado";

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  created_at: string;
}

export interface ReportType {
  id: string;
  name: string;
  description: string | null;
  active: boolean;
  created_at: string;
}

export interface ReportProperties {
  id: string;
  text: string;
  urgency: Urgency;
  status: ReportStatus;
  report_type_id: string;
  author_id: string;
  photo_url: string | null;
  created_at: string;
}

export interface ReportFeature {
  type: "Feature";
  geometry: {
    type: "Point";
    coordinates: [number, number]; // [lon, lat] per RFC 7946
  };
  properties: ReportProperties;
}

export interface ReportGeoJSON {
  type: "FeatureCollection";
  features: ReportFeature[];
}

export interface ReportDetail {
  id: string;
  text: string;
  lat: number;
  lon: number;
  urgency: Urgency;
  status: ReportStatus;
  report_type_id: string;
  author_id: string;
  photo_url: string | null;
  created_at: string;
}

export interface ReportSummary {
  id: string;
  text: string;
  urgency: Urgency;
  status: ReportStatus;
}

export interface Forwarding {
  id: string;
  institution: string;
  proposed_solution: string;
  status: ForwardingStatus;
  agent_id: string;
  reports: ReportSummary[];
  created_at: string;
  updated_at: string;
}

export interface CreateReportBody {
  text: string;
  lat: number;
  lon: number;
  urgency: Urgency;
  report_type_id: string;
  photo_url?: string;
}

export interface CreateForwardingBody {
  institution: string;
  proposed_solution: string;
  report_ids: string[];
}

export interface UpdateForwardingBody {
  institution?: string;
  proposed_solution?: string;
}

export interface ReportFilters {
  urgency?: Urgency;
  status?: ReportStatus;
  type_id?: string;
  since?: string;
  until?: string;
  bbox?: string;
}

export interface ForwardingFilters {
  status?: ForwardingStatus;
  skip?: number;
  limit?: number;
}
