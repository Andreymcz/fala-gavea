import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { CreateForwardingBody, ForwardingStatus, ForwardingFilters } from "@/lib/types";

export function useForwardings(filters: ForwardingFilters = {}) {
  return useQuery({
    queryKey: ["forwardings", filters],
    queryFn: () => api.getForwardings(filters),
    staleTime: 30_000,
  });
}

/** Public (no-auth) forwardings list — D-011. Omits agent_id. */
export function usePublicForwardings(status?: ForwardingStatus) {
  return useQuery({
    queryKey: ["forwardings", "public", status ?? null],
    queryFn: () => api.getPublicForwardings(status),
    staleTime: 30_000,
  });
}

/**
 * Encaminhamentos linked to a report (public). Lazy: pass enabled=false to
 * avoid firing one request per row on initial render.
 */
export function useReportForwardings(reportId: string | null, enabled = true) {
  return useQuery({
    queryKey: ["reports", "forwardings", reportId],
    queryFn: () => api.getReportForwardings(reportId!),
    enabled: enabled && !!reportId,
    staleTime: 30_000,
  });
}

export function useMyForwardings(enabled = true) {
  return useQuery({
    queryKey: ["forwardings", "mine"],
    queryFn: () => api.getMyForwardings(),
    staleTime: 30_000,
    enabled,
  });
}

export function useCreateForwarding() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateForwardingBody) => api.createForwarding(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reports"] });
      qc.invalidateQueries({ queryKey: ["forwardings"] });
    },
  });
}

export function useUpdateForwardingStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: ForwardingStatus }) =>
      api.updateForwardingStatus(id, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["forwardings"] });
    },
  });
}
