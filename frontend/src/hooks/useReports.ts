import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ReportFilters } from "@/lib/types";

export function useReports(filters: ReportFilters = {}) {
  return useQuery({
    queryKey: ["reports", filters],
    queryFn: () => api.getReportsGeoJSON(filters),
    staleTime: 30_000,
  });
}
