import type { ReportFeature } from "@/lib/types";
import { Badge } from "@/components/ui/badge";

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
      <p className="text-gray-400 text-xs">{dateStr}</p>
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
