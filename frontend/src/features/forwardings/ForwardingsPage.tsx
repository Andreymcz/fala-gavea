import { useState } from "react";
import { useForwardings } from "@/hooks/useForwardings";
import { ForwardingRow } from "./ForwardingRow";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import type { ForwardingStatus } from "@/lib/types";

export function ForwardingsPage() {
  const [statusFilter, setStatusFilter] = useState<ForwardingStatus | "">("");
  const { data: forwardings = [], isLoading } = useForwardings(
    statusFilter ? { status: statusFilter } : {},
  );

  return (
    <div className="flex flex-1 flex-col overflow-y-auto p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Encaminhamentos</h1>
        <div className="flex items-center gap-2">
          <Label className="text-sm">Status</Label>
          <Select
            value={statusFilter}
            onValueChange={(v) => setStatusFilter(v as ForwardingStatus | "")}
          >
            <SelectTrigger className="h-8 text-xs w-48">
              <SelectValue placeholder="Todos" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Todos</SelectItem>
              <SelectItem value="aguardando_solucao">Aguardando solução</SelectItem>
              <SelectItem value="solucao_em_andamento">Em andamento</SelectItem>
              <SelectItem value="finalizado">Finalizado</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-500">Carregando encaminhamentos...</p>
      ) : forwardings.length === 0 ? (
        <div className="flex flex-1 items-center justify-center">
          <p className="text-sm text-gray-500">Nenhum encaminhamento criado ainda.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-md border border-gray-200">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-3 text-left font-medium text-gray-600">Órgão</th>
                <th className="p-3 text-left font-medium text-gray-600">Relatos</th>
                <th className="p-3 text-left font-medium text-gray-600">Status</th>
                <th className="p-3 text-left font-medium text-gray-600">Data</th>
                <th className="p-3 text-left font-medium text-gray-600">Ações</th>
              </tr>
            </thead>
            <tbody>
              {forwardings.map((f) => (
                <ForwardingRow key={f.id} forwarding={f} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
