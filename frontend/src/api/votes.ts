import type { VoteSummary } from "@/lib/types";

const BASE_URL = (import.meta.env.VITE_API_URL as string) || "";

function segment(targetType: "report" | "forwarding"): string {
  return targetType === "report" ? "reports" : "forwardings";
}

export async function getVoteSummary(
  targetType: "report" | "forwarding",
  targetId: string,
): Promise<VoteSummary> {
  const res = await fetch(`${BASE_URL}/${segment(targetType)}/${targetId}/votes`);
  if (!res.ok) throw new Error("Failed to fetch vote summary");
  return res.json();
}

export async function castVote(
  targetType: "report" | "forwarding",
  targetId: string,
  value: 1 | -1,
  token: string,
): Promise<VoteSummary> {
  const res = await fetch(`${BASE_URL}/${segment(targetType)}/${targetId}/votes`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ value }),
  });
  if (!res.ok) throw new Error("Failed to cast vote");
  return res.json();
}

export async function retractVote(
  targetType: "report" | "forwarding",
  targetId: string,
  token: string,
): Promise<void> {
  const res = await fetch(`${BASE_URL}/${segment(targetType)}/${targetId}/votes`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok && res.status !== 404) throw new Error("Failed to retract vote");
}

export async function getVoteSummaryBatch(
  reportIds: string[],
  token?: string | null,
): Promise<Record<string, VoteSummary>> {
  if (reportIds.length === 0) return {};
  const params = new URLSearchParams({ ids: reportIds.join(",") });
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${BASE_URL}/votes/reports/summary?${params}`, { headers });
  if (!res.ok) throw new Error("Failed to fetch vote summaries");
  return res.json();
}
