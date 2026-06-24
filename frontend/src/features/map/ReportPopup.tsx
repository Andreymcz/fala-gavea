import { useState, useEffect } from "react";
import type { ReportFeature, VoteSummary } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { useReportForwardings } from "@/hooks/useForwardings";
import { useAuth } from "@/auth/AuthContext";
import { VoteButtons } from "@/components/VoteButtons";
import { getVoteSummary, castVote, retractVote } from "@/api/votes";

const URGENCY_LABEL: Record<string, string> = {
  alta: "Alta",
  media: "Média",
  baixa: "Baixa",
};

const STATUS_LABEL: Record<string, string> = {
  pendente: "Pendente",
  em_analise: "Em análise",
  encaminhado: "Encaminhado",
  resolvido: "Resolvido",
};

const FWD_STATUS_LABEL: Record<string, string> = {
  aguardando_solucao: "aguardando solução",
  solucao_em_andamento: "em andamento",
  finalizado: "finalizado",
};

interface ReportPopupProps {
  feature: ReportFeature;
  typeMap: Map<string, string>;
  isAgent?: boolean;
  isSelected?: boolean;
  onToggleSelect?: (id: string) => void;
}

export function ReportPopup({
  feature,
  typeMap,
  isAgent = false,
  isSelected = false,
  onToggleSelect,
}: ReportPopupProps) {
  const p = feature.properties;
  const typeName = typeMap.get(p.report_type_id) ?? p.report_type_id;
  const dateStr = new Date(p.created_at).toLocaleDateString("pt-BR");

  const { user, token } = useAuth();
  const [voteSummary, setVoteSummary] = useState<VoteSummary | null>(null);

  // Lazy: the popup only mounts when the marker is opened — one fetch per open is acceptable.
  const { data: forwardings = [] } = useReportForwardings(p.id);

  useEffect(() => {
    getVoteSummary("report", p.id).then(setVoteSummary).catch(() => {});
  }, [p.id]);

  async function handleVote(value: 1 | -1) {
    if (!token) return;
    const updated = await castVote("report", p.id, value, token);
    setVoteSummary(updated);
  }

  async function handleRetract() {
    if (!token) return;
    await retractVote("report", p.id, token);
    const updated = await getVoteSummary("report", p.id);
    setVoteSummary(updated);
  }

  return (
    <div className="min-w-[200px] space-y-1.5 text-sm">
      <p className="font-semibold">{typeName}</p>
      <p className="text-gray-700 line-clamp-3">{p.text}</p>
      <div className="flex flex-wrap gap-1">
        <Badge variant={`urgency-${p.urgency}` as Parameters<typeof Badge>[0]["variant"]}>
          Urgência: {URGENCY_LABEL[p.urgency]}
        </Badge>
        <Badge variant={`status-${p.status}` as Parameters<typeof Badge>[0]["variant"]}>
          {STATUS_LABEL[p.status]}
        </Badge>
      </div>
      {forwardings.length > 0 && (
        <div className="space-y-0.5 border-t border-gray-100 pt-1">
          {forwardings.map((f) => (
            <p key={f.id} className="text-xs text-gray-600">
              Encaminhado → {f.institution} · {FWD_STATUS_LABEL[f.status] ?? f.status}
            </p>
          ))}
        </div>
      )}
      <p className="text-gray-400 text-xs">{dateStr}</p>
      <VoteButtons
        summary={voteSummary}
        onVote={handleVote}
        onRetract={handleRetract}
        disabled={false}
        readOnly={!token || (user?.id != null && user.id === p.author_id)}
      />
      {isAgent && onToggleSelect && (
        <label className="flex items-center gap-1.5 cursor-pointer mt-1">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onToggleSelect(p.id)}
            className="h-4 w-4"
          />
          <span>{isSelected ? "Selecionado" : "Selecionar para encaminhar"}</span>
        </label>
      )}
    </div>
  );
}
