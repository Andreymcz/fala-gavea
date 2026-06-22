import { useNavigate } from "react-router-dom";
import { useCreateReport } from "@/hooks/useReports";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "@/components/ui/toast";
import { ReportFormFields } from "./ReportFormFields";
import { useReportForm } from "./useReportForm";

export function ReportFormPage() {
  const navigate = useNavigate();
  const { mutate: createReport, isPending } = useCreateReport();
  const form = useReportForm();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const body = form.buildBody();
    if (!body) return;
    createReport(body, {
      onSuccess: () => {
        toast("Relato registrado com sucesso!", "success");
        navigate("/");
      },
      onError: () => {
        toast("Erro ao registrar relato. Tente novamente.", "error");
      },
    });
  }

  return (
    <div className="flex flex-1 items-start justify-center p-4">
      <Card className="w-full max-w-lg mt-4">
        <CardHeader>
          <CardTitle>Registrar relato</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <ReportFormFields form={form} />
            <Button type="submit" className="w-full" disabled={isPending}>
              {isPending ? "Registrando..." : "Registrar relato"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
