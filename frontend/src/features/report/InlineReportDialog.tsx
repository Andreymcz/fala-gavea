import { useCreateReport } from "@/hooks/useReports";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/toast";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogClose,
} from "@/components/ui/dialog";
import { ReportFormFields } from "./ReportFormFields";
import { useReportForm } from "./useReportForm";

interface InlineReportDialogProps {
  open: boolean;
  /** Latitude of the clicked map point (decimal). */
  lat: number;
  /** Longitude of the clicked map point (decimal). */
  lon: number;
  onOpenChange: (open: boolean) => void;
  /** Called after a successful create so the host can refresh / clear the marker. */
  onCreated?: () => void;
}

/**
 * Inline relato creation dialog opened from a map click. The lat/lon are
 * prefilled from the clicked point but remain editable (and the shared
 * "Usar minha localização" geolocate option is available via ReportFormFields).
 */
export function InlineReportDialog({
  open,
  lat,
  lon,
  onOpenChange,
  onCreated,
}: InlineReportDialogProps) {
  const { mutate: createReport, isPending } = useCreateReport();
  // Remount the form (and its prefilled coords) whenever a new point is armed.
  const form = useReportForm({
    initialLat: lat.toFixed(6),
    initialLon: lon.toFixed(6),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const body = form.buildBody();
    if (!body) return;
    createReport(body, {
      onSuccess: () => {
        toast("Relato registrado com sucesso!", "success");
        onOpenChange(false);
        onCreated?.();
      },
      onError: () => {
        toast("Erro ao registrar relato. Tente novamente.", "error");
      },
    });
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Adicionar relato aqui</DialogTitle>
          <DialogDescription>
            Localização preenchida a partir do ponto clicado no mapa. Você pode ajustá-la abaixo.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <ReportFormFields form={form} />
          <div className="flex justify-end gap-2">
            <DialogClose asChild>
              <Button type="button" variant="ghost" size="sm">
                Cancelar
              </Button>
            </DialogClose>
            <Button type="submit" size="sm" disabled={isPending}>
              {isPending ? "Registrando..." : "Registrar relato"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
