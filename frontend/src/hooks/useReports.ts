import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ReportFilters, CreateReportBody } from "@/lib/types";

export function useReports(filters: ReportFilters = {}) {
  return useQuery({
    queryKey: ["reports", filters],
    queryFn: () => api.getReportsGeoJSON(filters),
    staleTime: 30_000,
  });
}

export function useCreateReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateReportBody) => api.createReport(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reports"] });
    },
  });
}
