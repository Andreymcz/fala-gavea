import { useUpdateForwardingStatus } from "@/hooks/useForwardings";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "@/components/ui/toast";
import type { ForwardingStatus } from "@/lib/types";

const STATUS_LABELS: Record<ForwardingStatus, string> = {
  aguardando_solucao: "Aguardando solução",
  solucao_em_andamento: "Solução em andamento",
  finalizado: "Finalizado",
};

interface StatusSelectProps {
  forwardingId: string;
  currentStatus: ForwardingStatus;
}

export function StatusSelect({ forwardingId, currentStatus }: StatusSelectProps) {
  const { mutate: updateStatus, isPending } = useUpdateForwardingStatus();

  function handleChange(value: string) {
    const newStatus = value as ForwardingStatus;
    if (newStatus === currentStatus) return;
    updateStatus(
      { id: forwardingId, status: newStatus },
      {
        onSuccess: () => toast("Status atualizado.", "success"),
        onError: () => toast("Erro ao atualizar status.", "error"),
      },
    );
  }

  return (
    <Select value={currentStatus} onValueChange={handleChange} disabled={isPending}>
      <SelectTrigger className="h-8 text-xs w-48">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {(Object.entries(STATUS_LABELS) as [ForwardingStatus, string][]).map(([value, label]) => (
          <SelectItem key={value} value={value}>
            {label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
