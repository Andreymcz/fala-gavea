import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useReportTypes() {
  return useQuery({
    queryKey: ["reportTypes"],
    queryFn: () => api.getReportTypes(),
    staleTime: 5 * 60_000, // 5 minutes — types change rarely
  });
}
