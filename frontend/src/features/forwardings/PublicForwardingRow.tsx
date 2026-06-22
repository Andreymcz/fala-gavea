import { useState } from "react";
import type { PublicForwarding, ForwardingStatus } from "@/lib/types";
import { Badge } from "@/components/ui/badge";

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
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
