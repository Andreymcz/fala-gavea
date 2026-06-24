import type { VoteSummary } from "@/lib/types";

const BASE_URL = (import.meta.env.VITE_API_URL as string) || "";

export async function getVoteSummary(
  targetType: "report" | "forwarding",
  targetId: string,
): Promise<VoteSummary> {
  const res = await fetch(`${BASE_URL}/votes/${targetType}/${targetId}/summary`);
  if (!res.ok) throw new Error("Failed to fetch vote summary");
  return res.json();
}

export async function castVote(
  targetType: "report" | "forwarding",
  targetId: string,
  value: 1 | -1,
  token: string,
): Promise<VoteSummary> {
  const res = await fetch(`${BASE_URL}/votes`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ target_type: targetType, target_id: targetId, value }),
  });
  if (!res.ok) throw new Error("Failed to cast vote");
  return res.json();
}

export async function retractVote(
  targetType: "report" | "forwarding",
  targetId: string,
  token: string,
): Promise<void> {
  const res = await fetch(`${BASE_URL}/votes/${targetType}/${targetId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok && res.status !== 404) throw new Error("Failed to retract vote");
}
