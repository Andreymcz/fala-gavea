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
