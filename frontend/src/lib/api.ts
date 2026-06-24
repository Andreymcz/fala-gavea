import type {
  User,
  ReportType,
  ReportGeoJSON,
  ReportDetail,
  Forwarding,
  CreateReportBody,
  CreateForwardingBody,
  UpdateForwardingBody,
  ReportFilters,
  ForwardingFilters,
  ForwardingStatus,
  PublicForwarding,
  KeywordListResponse,
  ReportSearchResult,
  ChatRequest,
  ChatResponse,
  ReportQueryBody,
  ReportQueryResponse,
  SavedFilter,
  SavedFilterCreate,
  SavedFilterUpdate,
} from "./types";

const BASE_URL = (import.meta.env.VITE_API_URL as string) || "";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

function getToken(): string | null {
  return localStorage.getItem("fala_gavea_token");
}

async function request<T>(
  method: string,
  path: string,
  options: {
    body?: unknown;
    formData?: URLSearchParams;
    public?: boolean;
  } = {},
): Promise<T> {
  const headers: Record<string, string> = {};
  let body: BodyInit | undefined;

  if (options.formData) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    body = options.formData;
  } else if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.body);
  }

  if (!options.public) {
    const token = getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const res = await fetch(`${BASE_URL}${path}`, { method, headers, body });

  if (res.status === 401) {
    const data = await res.json().catch(() => ({ detail: "Unauthorized" }));
    window.dispatchEvent(new Event("auth:unauthorized"));
    throw new ApiError(401, data.detail || "Unauthorized");
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, data.detail || res.statusText);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") {
      p.append(k, String(v));
    }
  }
  const s = p.toString();
  return s ? `?${s}` : "";
}

export const api = {
  login(email: string, password: string): Promise<{ access_token: string }> {
    const formData = new URLSearchParams({ username: email, password });
    return request<{ access_token: string }>("POST", "/auth/token", { formData, public: true });
  },

  register(data: { email: string; password: string; name: string }): Promise<User> {
    return request<User>("POST", "/auth/register", { body: data, public: true });
  },

  me(): Promise<User> {
    return request<User>("GET", "/auth/me");
  },

  getReportsGeoJSON(filters: ReportFilters = {}): Promise<ReportGeoJSON> {
    const q = buildQuery(filters as Record<string, string | undefined>);
    return request<ReportGeoJSON>("GET", `/reports/geojson${q}`, { public: true });
  },

  getReport(id: string): Promise<ReportDetail> {
    return request<ReportDetail>("GET", `/reports/${id}`);
  },

  createReport(body: CreateReportBody): Promise<ReportDetail> {
    return request<ReportDetail>("POST", "/reports", { body });
  },

  getReportTypes(): Promise<ReportType[]> {
    return request<ReportType[]>("GET", "/report_types/", { public: true });
  },

  getForwardings(filters: ForwardingFilters = {}): Promise<Forwarding[]> {
    const q = buildQuery(filters as Record<string, string | number | undefined>);
    return request<Forwarding[]>("GET", `/forwardings${q}`);
  },

  getForwarding(id: string): Promise<Forwarding> {
    return request<Forwarding>("GET", `/forwardings/${id}`);
  },

  getPublicForwardings(status?: ForwardingStatus): Promise<PublicForwarding[]> {
    const q = buildQuery({ status });
    return request<PublicForwarding[]>("GET", `/forwardings/public${q}`, { public: true });
  },

  getPublicForwarding(id: string): Promise<PublicForwarding> {
    return request<PublicForwarding>("GET", `/forwardings/public/${id}`, { public: true });
  },

  getReportForwardings(reportId: string): Promise<PublicForwarding[]> {
    return request<PublicForwarding[]>("GET", `/reports/${reportId}/forwardings`, { public: true });
  },

  createForwarding(body: CreateForwardingBody): Promise<Forwarding> {
    return request<Forwarding>("POST", "/forwardings", { body });
  },

  updateForwardingStatus(id: string, status: ForwardingStatus): Promise<Forwarding> {
    return request<Forwarding>("PATCH", `/forwardings/${id}/status`, { body: { status } });
  },

  updateForwarding(id: string, body: UpdateForwardingBody): Promise<Forwarding> {
    return request<Forwarding>("PATCH", `/forwardings/${id}`, { body });
  },

  getKeywords(filters: ReportFilters, min_docs?: number): Promise<KeywordListResponse> {
    const q = buildQuery({ ...(filters as Record<string, string | number | undefined>), min_docs: min_docs ?? 3 });
    return request<KeywordListResponse>("GET", `/reports/keywords${q}`);
  },

  getSimilarReports(id: string, n?: number): Promise<ReportSearchResult[]> {
    const q = buildQuery({ n: n ?? 5 });
    return request<ReportSearchResult[]>("GET", `/reports/${id}/similar${q}`);
  },

  similarToSet(reportIds: string[], n?: number): Promise<ReportSearchResult[]> {
    return request<ReportSearchResult[]>("POST", "/reports/similar-to-set", {
      body: { report_ids: reportIds, ...(n != null ? { n } : {}) },
    });
  },

  searchReports(q: string, n?: number): Promise<ReportSearchResult[]> {
    const qs = buildQuery({ q, n: n ?? 50 });
    return request<ReportSearchResult[]>("GET", `/reports/search${qs}`, { public: true });
  },

  queryReports(body: ReportQueryBody): Promise<ReportQueryResponse> {
    return request<ReportQueryResponse>("POST", "/reports/query", { body });
  },

  chat(body: ChatRequest): Promise<ChatResponse> {
    return request<ChatResponse>("POST", "/nl/chat", { body });
  },

  seedTopicos(file: File): Promise<{ inserted: number; skipped: number; errors: unknown[] }> {
    const token = getToken();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const formData = new FormData();
    formData.append("file", file);
    return fetch(`${BASE_URL}/admin/seed/topicos`, { method: "POST", headers, body: formData }).then(
      async (res) => {
        if (!res.ok) {
          const data = await res.json().catch(() => ({ detail: res.statusText }));
          throw new ApiError(res.status, data.detail || res.statusText);
        }
        return res.json();
      },
    );
  },

  seedRelatos(file: File): Promise<{ inserted: number; skipped: number; errors: unknown[] }> {
    const token = getToken();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const formData = new FormData();
    formData.append("file", file);
    return fetch(`${BASE_URL}/admin/seed/relatos`, { method: "POST", headers, body: formData }).then(
      async (res) => {
        if (!res.ok) {
          const data = await res.json().catch(() => ({ detail: res.statusText }));
          throw new ApiError(res.status, data.detail || res.statusText);
        }
        return res.json();
      },
    );
  },

  createSavedFilter(data: SavedFilterCreate): Promise<SavedFilter> {
    return request<SavedFilter>("POST", "/saved-filters", { body: data });
  },

  listSavedFilters(): Promise<SavedFilter[]> {
    return request<SavedFilter[]>("GET", "/saved-filters");
  },

  getSavedFilter(id: string): Promise<SavedFilter> {
    return request<SavedFilter>("GET", `/saved-filters/${id}`);
  },

  updateSavedFilter(id: string, data: SavedFilterUpdate): Promise<SavedFilter> {
    return request<SavedFilter>("PATCH", `/saved-filters/${id}`, { body: data });
  },

  deleteSavedFilter(id: string): Promise<void> {
    return request<void>("DELETE", `/saved-filters/${id}`);
  },

  getMyAnonymousReports(token: string): Promise<ReportDetail[]> {
    return request<ReportDetail[]>("GET", `/reports/mine?anonymous_token=${encodeURIComponent(token)}`, { public: true });
  },

  wipeDatabase(
    includeReportTypes: boolean,
  ): Promise<{ wiped: { reports: number; forwardings: number; report_types: number } }> {
    return request("DELETE", `/admin/seed/wipe?include_report_types=${includeReportTypes}`);
  },
};
