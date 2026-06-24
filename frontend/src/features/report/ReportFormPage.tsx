import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useCreateReport } from "@/hooks/useReports";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "@/components/ui/toast";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ReportFormFields } from "./ReportFormFields";
import { useReportForm } from "./useReportForm";
import { useAuth } from "@/auth/AuthContext";

export function ReportFormPage() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const { mutate: createReport, isPending } = useCreateReport();
  const form = useReportForm();

  const [anonymous, setAnonymous] = useState(false);
  const [showTokenDialog, setShowTokenDialog] = useState(false);
  const [claimToken, setClaimToken] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Not logged in and not in anonymous mode — show login prompt
  if (!token && !anonymous) {
    return (
      <div className="flex flex-1 items-start justify-center p-4">
        <Card className="w-full max-w-lg mt-4">
          <CardHeader>
            <CardTitle>Registrar relato</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-gray-700">
              Você precisa fazer login para enviar um relato identificado.{" "}
              <Link to="/login" className="text-blue-600 hover:underline">
                Entrar
              </Link>{" "}
              ou ative abaixo &ldquo;Enviar sem identificação&rdquo; para enviar anonimamente.
            </p>
            <label className="flex items-center gap-3 cursor-pointer">
              <span className="relative inline-flex items-center">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={anonymous}
                  onChange={(e) => setAnonymous(e.target.checked)}
                />
                <div className="w-10 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-blue-400 rounded-full peer peer-checked:bg-blue-600 transition-colors" />
                <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full peer-checked:translate-x-4 transition-transform" />
              </span>
              <span className="text-sm font-medium text-gray-700">Enviar sem identificação</span>
            </label>
          </CardContent>
        </Card>
      </div>
    );
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const body = form.buildBody();
    if (!body) return;
    createReport(
      { ...body, anonymous: anonymous || undefined },
      {
        onSuccess: (response) => {
          if (response.anonymous_claim_token) {
            setClaimToken(response.anonymous_claim_token);
            setShowTokenDialog(true);
          } else {
            toast("Relato registrado com sucesso!", "success");
            navigate("/");
          }
        },
        onError: () => {
          toast("Erro ao registrar relato. Tente novamente.", "error");
        },
      },
    );
  }

  function handleCopy() {
    if (!claimToken) return;
    navigator.clipboard.writeText(claimToken).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  function handleClose() {
    if (claimToken) {
      localStorage.setItem("fala_gavea_anon_token", claimToken);
    }
    setShowTokenDialog(false);
    navigate("/");
  }

  return (
    <div className="flex flex-1 items-start justify-center p-4">
      <Card className="w-full max-w-lg mt-4">
        <CardHeader>
          <CardTitle>Registrar relato</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Anonymous toggle */}
            <div className="space-y-1.5">
              <label className="flex items-center gap-3 cursor-pointer">
                <span className="relative inline-flex items-center">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={anonymous}
                    onChange={(e) => setAnonymous(e.target.checked)}
                  />
                  <div className="w-10 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-blue-400 rounded-full peer peer-checked:bg-blue-600 transition-colors" />
                  <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full peer-checked:translate-x-4 transition-transform" />
                </span>
                <span className="text-sm font-medium text-gray-700">Enviar sem identificação</span>
              </label>
              {anonymous && (
                <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2">
                  Ao enviar sem identificação, você receberá um código para acompanhar seu relato.
                  Guarde esse código — sem ele não será possível acompanhar o andamento.
                </p>
              )}
            </div>

            <ReportFormFields form={form} />
            <Button type="submit" className="w-full" disabled={isPending}>
              {isPending ? "Registrando..." : "Registrar relato"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Anonymous claim token dialog */}
      <Dialog open={showTokenDialog} onOpenChange={() => {}}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Seu relato foi enviado!</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-gray-600">Código de acompanhamento:</p>
          <div className="flex items-center gap-2 rounded border border-gray-200 p-2 font-mono text-sm bg-gray-50">
            <span className="flex-1 break-all">{claimToken}</span>
            <button
              type="button"
              onClick={handleCopy}
              className="ml-auto text-blue-600 text-xs hover:underline whitespace-nowrap"
            >
              {copied ? "Copiado!" : "Copiar código"}
            </button>
          </div>
          <p className="text-xs text-amber-600">
            Guarde este código — sem ele não será possível acompanhar o andamento do seu relato
            anônimo.
          </p>
          <button
            type="button"
            onClick={handleClose}
            className="mt-2 w-full rounded bg-blue-600 py-2 text-sm text-white hover:bg-blue-700"
          >
            Fechar
          </button>
        </DialogContent>
      </Dialog>
    </div>
  );
}
