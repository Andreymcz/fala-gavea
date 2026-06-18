import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useReportTypes } from "@/hooks/useReportTypes";
import { useCreateReport } from "@/hooks/useReports";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "@/components/ui/toast";
import type { Urgency } from "@/lib/types";

interface FormErrors {
  text?: string;
  lat?: string;
  lon?: string;
  report_type_id?: string;
  urgency?: string;
}

export function ReportFormPage() {
  const navigate = useNavigate();
  const { data: reportTypes = [], isLoading: typesLoading } = useReportTypes();
  const { mutate: createReport, isPending } = useCreateReport();

  const [text, setText] = useState("");
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [urgency, setUrgency] = useState<Urgency | "">("");
  const [reportTypeId, setReportTypeId] = useState("");
  const [photoUrl, setPhotoUrl] = useState("");
  const [geoError, setGeoError] = useState<string | null>(null);
  const [geoLoading, setGeoLoading] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});

  function validate(): boolean {
    const errs: FormErrors = {};
    if (text.trim().length < 10)
      errs.text = "Descrição deve ter pelo menos 10 caracteres.";
    if (text.trim().length > 2000)
      errs.text = "Descrição deve ter no máximo 2000 caracteres.";
    const latNum = parseFloat(lat);
    const lonNum = parseFloat(lon);
    if (!lat || isNaN(latNum) || latNum < -90 || latNum > 90)
      errs.lat = "Latitude inválida (deve ser entre -90 e 90).";
    if (!lon || isNaN(lonNum) || lonNum < -180 || lonNum > 180)
      errs.lon = "Longitude inválida (deve ser entre -180 e 180).";
    if (!reportTypeId) errs.report_type_id = "Selecione o tipo de problema.";
    if (!urgency) errs.urgency = "Selecione a urgência.";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  function handleGeolocate() {
    if (!navigator.geolocation) {
      setGeoError("Geolocalização não disponível. Preencha latitude e longitude manualmente.");
      return;
    }
    setGeoLoading(true);
    setGeoError(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLat(pos.coords.latitude.toFixed(6));
        setLon(pos.coords.longitude.toFixed(6));
        setGeoLoading(false);
      },
      () => {
        setGeoError("Geolocalização não disponível. Preencha latitude e longitude manualmente.");
        setGeoLoading(false);
      },
    );
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    createReport(
      {
        text: text.trim(),
        lat: parseFloat(lat),
        lon: parseFloat(lon),
        urgency: urgency as Urgency,
        report_type_id: reportTypeId,
        photo_url: photoUrl.trim() || undefined,
      },
      {
        onSuccess: () => {
          toast("Relato registrado com sucesso!", "success");
          navigate("/");
        },
        onError: () => {
          toast("Erro ao registrar relato. Tente novamente.", "error");
        },
      },
    );
  }

  return (
    <div className="flex flex-1 items-start justify-center p-4">
      <Card className="w-full max-w-lg mt-4">
        <CardHeader>
          <CardTitle>Registrar relato</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1">
              <Label htmlFor="report_type">Tipo de problema</Label>
              <Select value={reportTypeId} onValueChange={setReportTypeId}>
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
              {errors.report_type_id && (
                <p role="alert" className="text-xs text-red-600">{errors.report_type_id}</p>
              )}
            </div>

            <div className="space-y-1">
              <Label htmlFor="urgency">Urgência</Label>
              <Select value={urgency} onValueChange={(v) => setUrgency(v as Urgency)}>
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
              {errors.urgency && (
                <p role="alert" className="text-xs text-red-600">{errors.urgency}</p>
              )}
            </div>

            <div className="space-y-1">
              <Label htmlFor="text">Descrição do problema</Label>
              <Textarea
                id="text"
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={4}
                placeholder="Descreva o problema com detalhes. Ex: Poste apagado na esquina da rua X com rua Y, colocando pedestres em risco."
                minLength={10}
                maxLength={2000}
              />
              <p className="text-xs text-gray-400">{text.length}/2000 caracteres</p>
              {errors.text && (
                <p role="alert" className="text-xs text-red-600">{errors.text}</p>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Localização</Label>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={handleGeolocate}
                  disabled={geoLoading}
                >
                  {geoLoading ? "Obtendo localização..." : "Usar minha localização"}
                </Button>
              </div>
              {geoError && (
                <p role="alert" className="text-xs text-amber-600">{geoError}</p>
              )}
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label htmlFor="lat" className="text-xs">Latitude</Label>
                  <Input
                    id="lat"
                    type="number"
                    step="any"
                    value={lat}
                    onChange={(e) => setLat(e.target.value)}
                    placeholder="-22.9731"
                  />
                  {errors.lat && (
                    <p role="alert" className="text-xs text-red-600">{errors.lat}</p>
                  )}
                </div>
                <div className="space-y-1">
                  <Label htmlFor="lon" className="text-xs">Longitude</Label>
                  <Input
                    id="lon"
                    type="number"
                    step="any"
                    value={lon}
                    onChange={(e) => setLon(e.target.value)}
                    placeholder="-43.2272"
                  />
                  {errors.lon && (
                    <p role="alert" className="text-xs text-red-600">{errors.lon}</p>
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-1">
              <Label htmlFor="photo_url">URL da foto (opcional)</Label>
              <Input
                id="photo_url"
                type="url"
                value={photoUrl}
                onChange={(e) => setPhotoUrl(e.target.value)}
                placeholder="Cole a URL de uma foto do problema"
              />
            </div>

            <Button type="submit" className="w-full" disabled={isPending}>
              {isPending ? "Registrando..." : "Registrar relato"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
