import { useReportTypes } from "@/hooks/useReportTypes";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { Urgency } from "@/lib/types";
import type { UseReportFormResult } from "./useReportForm";

interface ReportFormFieldsProps {
  form: UseReportFormResult;
}

/**
 * Shared report form fields (type, urgency, description, location, photo).
 * Renders against a `useReportForm` instance so the standalone page and the
 * inline map-click dialog stay in sync. Does NOT render a submit button or a
 * surrounding <form> — the host owns submission.
 */
export function ReportFormFields({ form }: ReportFormFieldsProps) {
  const { data: reportTypes = [], isLoading: typesLoading } = useReportTypes();

  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <Label htmlFor="report_type">Tipo de problema</Label>
        <Select value={form.reportTypeId} onValueChange={form.setReportTypeId}>
          <SelectTrigger id="report_type">
            <SelectValue placeholder={typesLoading ? "Carregando..." : "Selecione o tipo"} />
          </SelectTrigger>
          <SelectContent>
            {reportTypes.map((rt) => (
              <SelectItem key={rt.id} value={rt.id}>
                {rt.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {form.errors.report_type_id && (
          <p role="alert" className="text-xs text-red-600">{form.errors.report_type_id}</p>
        )}
      </div>

      <div className="space-y-1">
        <Label htmlFor="urgency">Urgência</Label>
        <Select value={form.urgency} onValueChange={(v) => form.setUrgency(v as Urgency)}>
          <SelectTrigger id="urgency">
            <SelectValue placeholder="Selecione a urgência" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="alta">
              <span className="flex items-center gap-2">
                <span className="inline-block h-2 w-2 rounded-full bg-[#E53E3E]" />
                Alta
              </span>
            </SelectItem>
            <SelectItem value="media">
              <span className="flex items-center gap-2">
                <span className="inline-block h-2 w-2 rounded-full bg-[#DD6B20]" />
                Média
              </span>
            </SelectItem>
            <SelectItem value="baixa">
              <span className="flex items-center gap-2">
                <span className="inline-block h-2 w-2 rounded-full bg-[#3182CE]" />
                Baixa
              </span>
            </SelectItem>
          </SelectContent>
        </Select>
        {form.errors.urgency && (
          <p role="alert" className="text-xs text-red-600">{form.errors.urgency}</p>
        )}
      </div>

      <div className="space-y-1">
        <Label htmlFor="text">Descrição do problema</Label>
        <Textarea
          id="text"
          value={form.text}
          onChange={(e) => form.setText(e.target.value)}
          rows={4}
          placeholder="Descreva o problema com detalhes. Ex: Poste apagado na esquina da rua X com rua Y, colocando pedestres em risco."
          minLength={10}
          maxLength={2000}
        />
        <p className="text-xs text-gray-400">{form.text.length}/2000 caracteres</p>
        {form.errors.text && (
          <p role="alert" className="text-xs text-red-600">{form.errors.text}</p>
        )}
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label>Localização</Label>
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={form.handleGeolocate}
            disabled={form.geoLoading}
          >
            {form.geoLoading ? "Obtendo localização..." : "Usar minha localização"}
          </Button>
        </div>
        {form.geoError && (
          <p role="alert" className="text-xs text-amber-600">{form.geoError}</p>
        )}
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <Label htmlFor="lat" className="text-xs">Latitude</Label>
            <Input
              id="lat"
              type="number"
              step="any"
              value={form.lat}
              onChange={(e) => form.setLat(e.target.value)}
              placeholder="-22.9731"
            />
            {form.errors.lat && (
              <p role="alert" className="text-xs text-red-600">{form.errors.lat}</p>
            )}
          </div>
          <div className="space-y-1">
            <Label htmlFor="lon" className="text-xs">Longitude</Label>
            <Input
              id="lon"
              type="number"
              step="any"
              value={form.lon}
              onChange={(e) => form.setLon(e.target.value)}
              placeholder="-43.2272"
            />
            {form.errors.lon && (
              <p role="alert" className="text-xs text-red-600">{form.errors.lon}</p>
            )}
          </div>
        </div>
      </div>

      <div className="space-y-1">
        <Label htmlFor="photo_url">URL da foto (opcional)</Label>
        <Input
          id="photo_url"
          type="url"
          value={form.photoUrl}
          onChange={(e) => form.setPhotoUrl(e.target.value)}
          placeholder="Cole a URL de uma foto do problema"
        />
      </div>
    </div>
  );
}
