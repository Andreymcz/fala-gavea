import { useState, useEffect } from "react";
import type { PublicForwarding, ForwardingStatus, VoteSummary } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { VoteButtons } from "@/components/VoteButtons";
import { useAuth } from "@/auth/AuthContext";
import { castVote, retractVote, getVoteSummary } from "@/api/votes";

const FWD_STATUS_LABELS: Record<ForwardingStatus, string> = {
  aguardando_solucao: "Aguardando solução",
  solucao_em_andamento: "Em andamento",
  finalizado: "Finalizado",
};

const URGENCY_LABELS: Record<string, string> = {
  alta: "Alta",
  media: "Média",
  baixa: "Baixa",
};

interface PublicForwardingRowProps {
  forwarding: PublicForwarding;
}

/** Read-only forwarding row for the public transparency view (no edit actions, no agent_id). */
export function PublicForwardingRow({ forwarding }: PublicForwardingRowProps) {
  const [expanded, setExpanded] = useState(false);
  const date = new Date(forwarding.created_at).toLocaleDateString("pt-BR");

  const { token } = useAuth();
  const [voteSummary, setVoteSummary] = useState<VoteSummary | null>(null);
  const [voteLoading, setVoteLoading] = useState(false);

  // Fetch vote summary when expanded
  useEffect(() => {
    if (expanded) {
      getVoteSummary("forwarding", forwarding.id)
        .then(setVoteSummary)
        .catch(() => {});
    }
  }, [expanded, forwarding.id]);

  async function handleVote(value: 1 | -1) {
    if (!token) return;
    setVoteLoading(true);
    try {
      const updated = await castVote("forwarding", forwarding.id, value, token);
      setVoteSummary(updated);
    } catch (_) {} finally {
      setVoteLoading(false);
    }
  }

  async function handleRetract() {
    if (!token) return;
    setVoteLoading(true);
    try {
      await retractVote("forwarding", forwarding.id, token);
      const updated = await getVoteSummary("forwarding", forwarding.id);
      setVoteSummary(updated);
    } catch (_) {} finally {
      setVoteLoading(false);
    }
  }

  return (
    <>
      <tr
        className="border-b transition-colors hover:bg-gray-50 cursor-pointer"
        onClick={() => setExpanded((v) => !v)}
      >
        <td className="p-3 text-sm font-medium">{forwarding.institution}</td>
        <td className="p-3 text-sm text-gray-600">{forwarding.reports.length}</td>
        <td className="p-3">
          <Badge variant={`fwd-${forwarding.status}` as Parameters<typeof Badge>[0]["variant"]}>
            {FWD_STATUS_LABELS[forwarding.status]}
          </Badge>
        </td>
        <td className="p-3 text-sm text-gray-500">{date}</td>
      </tr>
      {expanded && (
        <tr className="bg-gray-50">
          <td colSpan={4} className="px-4 pb-3">
            <div className="space-y-2 pt-2">
              <div>
                <p className="text-xs font-semibold text-gray-500 mb-1">Solução proposta:</p>
                <p className="text-xs text-gray-700 whitespace-pre-line">
                  {forwarding.proposed_solution}
                </p>
              </div>
              {forwarding.reports.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 mb-1">Relatos incluídos:</p>
                  {forwarding.reports.map((r) => (
                    <div key={r.id} className="flex items-center gap-2 text-xs text-gray-700">
                      <Badge variant={`urgency-${r.urgency}` as Parameters<typeof Badge>[0]["variant"]}>
                        {URGENCY_LABELS[r.urgency] ?? r.urgency}
                      </Badge>
                      <span className="line-clamp-1">{r.text}</span>
                    </div>
                  ))}
                </div>
              )}
              <div className="flex items-center gap-2 pt-1 border-t border-gray-200">
                <span className="text-xs text-gray-500">Votos:</span>
                <VoteButtons
                  summary={voteSummary}
                  onVote={handleVote}
                  onRetract={handleRetract}
                  disabled={!token}
                  loading={voteLoading}
                />
                {!token && (
                  <span className="text-xs text-gray-400">
                    ▲ {voteSummary?.upvotes ?? 0} &nbsp; ▼ {voteSummary?.downvotes ?? 0}
                  </span>
                )}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
