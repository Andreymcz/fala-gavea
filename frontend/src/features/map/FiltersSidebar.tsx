import type { Urgency, ReportStatus, ReportType } from "@/lib/types";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export interface MapFilters {
  urgency?: Urgency | "";
  status?: ReportStatus | "";
  type_id?: string;
  since?: string;
  until?: string;
}

interface FiltersSidebarProps {
  filters: MapFilters;
  onChange: (filters: MapFilters) => void;
  reportTypes: ReportType[];
}

export function FiltersSidebar({ filters, onChange, reportTypes }: FiltersSidebarProps) {
  function update(patch: Partial<MapFilters>) {
    onChange({ ...filters, ...patch });
  }

  function clearAll() {
    onChange({});
  }

  return (
    <div className="flex flex-col gap-3 p-3 bg-white border-r border-gray-200 w-56 overflow-y-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700">Filtros</h2>
        <Button variant="ghost" size="sm" onClick={clearAll} className="text-xs h-7 px-2">
          Limpar
        </Button>
      </div>

      <div className="space-y-1">
        <Label className="text-xs">Tipo</Label>
        <Select value={filters.type_id ?? ""} onValueChange={(v) => update({ type_id: v || undefined })}>
          <SelectTrigger className="h-8 text-xs">
            <SelectValue placeholder="Todos os tipos" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Todos os tipos</SelectItem>
            {reportTypes.map((rt) => (
              <SelectItem key={rt.id} value={rt.id}>
                {rt.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1">
        <Label className="text-xs">Urgência</Label>
        <Select
          value={filters.urgency ?? ""}
          onValueChange={(v) => update({ urgency: (v as Urgency) || undefined })}
        >
          <SelectTrigger className="h-8 text-xs">
            <SelectValue placeholder="Todas" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Todas</SelectItem>
            <SelectItem value="alta">Alta</SelectItem>
            <SelectItem value="media">Média</SelectItem>
            <SelectItem value="baixa">Baixa</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1">
        <Label className="text-xs">Status</Label>
        <Select
          value={filters.status ?? ""}
          onValueChange={(v) => update({ status: (v as ReportStatus) || undefined })}
        >
          <SelectTrigger className="h-8 text-xs">
            <SelectValue placeholder="Todos" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Todos</SelectItem>
            <SelectItem value="pendente">Pendente</SelectItem>
            <SelectItem value="em_analise">Em análise</SelectItem>
            <SelectItem value="encaminhado">Encaminhado</SelectItem>
            <SelectItem value="resolvido">Resolvido</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1">
        <Label className="text-xs">De</Label>
        <Input
          type="date"
          className="h-8 text-xs"
          value={filters.since ?? ""}
          onChange={(e) => update({ since: e.target.value || undefined })}
        />
      </div>

      <div className="space-y-1">
        <Label className="text-xs">Até</Label>
        <Input
          type="date"
          className="h-8 text-xs"
          value={filters.until ?? ""}
          onChange={(e) => update({ until: e.target.value || undefined })}
        />
      </div>

      {/* Wave-2 placeholder: semantic search (disabled) */}
      <div className="space-y-1 mt-2 opacity-50 cursor-not-allowed" title="Disponível em breve">
        <Label className="text-xs">Busca semântica</Label>
        <Input
          className="h-8 text-xs"
          placeholder="Busca semântica (em breve)"
          disabled
          aria-disabled="true"
        />
      </div>
    </div>
  );
}
