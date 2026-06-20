import { useRef, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "@/components/ui/toast";
import { api, ApiError } from "@/lib/api";

type WipeScope = "reports" | "all";

export function AdminPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [seeding, setSeeding] = useState(false);

  const relatosInputRef = useRef<HTMLInputElement>(null);
  const [relatosFile, setRelatosFile] = useState<File | null>(null);
  const [seedingRelatos, setSeedingRelatos] = useState(false);

  const [wipeScope, setWipeScope] = useState<WipeScope | null>(null);
  const [wiping, setWiping] = useState(false);

  function handleSeedSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      toast("Selecione um arquivo CSV.", "error");
      return;
    }
    setSeeding(true);
    api
      .seedTopicos(file)
      .then((res) => {
        toast(`${res.inserted} tópicos inseridos, ${res.skipped} ignorados.`, "success");
        setFile(null);
        if (fileInputRef.current) fileInputRef.current.value = "";
      })
      .catch((err) => {
        const msg = err instanceof ApiError ? err.detail : "Erro ao processar o arquivo.";
        toast(`Falha ao inserir tópicos: ${msg}`, "error");
      })
      .finally(() => setSeeding(false));
  }

  function handleSeedRelatosSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!relatosFile) {
      toast("Selecione um arquivo CSV.", "error");
      return;
    }
    setSeedingRelatos(true);
    api
      .seedRelatos(relatosFile)
      .then((res) => {
        toast(`${res.inserted} relatos inseridos, ${res.skipped} ignorados.`, "success");
        setRelatosFile(null);
        if (relatosInputRef.current) relatosInputRef.current.value = "";
      })
      .catch((err) => {
        const msg = err instanceof ApiError ? err.detail : "Erro ao processar o arquivo.";
        toast(`Falha ao inserir relatos: ${msg}`, "error");
      })
      .finally(() => setSeedingRelatos(false));
  }

  function handleWipeConfirm() {
    if (wipeScope === null) return;
    const includeReportTypes = wipeScope === "all";
    setWiping(true);
    api
      .wipeDatabase(includeReportTypes)
      .then((res) => {
        const { reports, forwardings, report_types } = res.wiped;
        toast(
          `Banco limpo: ${reports} relatos, ${forwardings} encaminhamentos, ${report_types} tópicos.`,
          "success",
        );
        setWipeScope(null);
      })
      .catch((err) => {
        const msg = err instanceof ApiError ? err.detail : "Erro ao limpar o banco.";
        toast(`Falha ao limpar o banco: ${msg}`, "error");
      })
      .finally(() => setWiping(false));
  }

  const wipeDescription =
    wipeScope === "all"
      ? "Isto vai apagar permanentemente todos os relatos, encaminhamentos e tópicos. Esta ação não pode ser desfeita."
      : "Isto vai apagar permanentemente todos os relatos e encaminhamentos. Os tópicos serão mantidos. Esta ação não pode ser desfeita.";

  return (
    <div className="flex flex-1 flex-col p-6">
      <h1 className="mb-6 text-xl font-semibold text-gray-900">Painel administrativo</h1>

      <div className="flex max-w-2xl flex-col gap-6">
        <section className="rounded-md border border-gray-200 p-5">
          <h2 className="mb-1 text-base font-semibold text-gray-900">Seed de Tópicos</h2>
          <p className="mb-4 text-sm text-gray-500">
            Envie um arquivo CSV com colunas <code>nome</code> e <code>descricao</code> para criar
            tópicos em massa.
          </p>
          <form onSubmit={handleSeedSubmit} className="flex flex-col gap-3">
            <div className="space-y-1">
              <Label htmlFor="seed-file">Arquivo CSV</Label>
              <Input
                id="seed-file"
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </div>
            <div>
              <Button type="submit" disabled={seeding || !file}>
                {seeding ? "Enviando..." : "Enviar CSV"}
              </Button>
            </div>
          </form>
        </section>

        <section className="rounded-md border border-gray-200 p-5">
          <h2 className="mb-1 text-base font-semibold text-gray-900">Seed de Relatos</h2>
          <p className="mb-3 text-sm text-gray-500">
            Envie um CSV com as colunas{" "}
            <code>user_id, texto_relato, latitude, longitude, data, topico, urgency</code>. Apenas{" "}
            <strong>user_id</strong> é obrigatório. Regras automáticas:
          </p>
          <ul className="mb-4 list-disc space-y-1 pl-5 text-sm text-gray-500">
            <li>
              <strong>Usuário:</strong> se o <code>user_id</code> não existir, criamos uma conta de
              cidadão automaticamente (senha padrão de desenvolvimento).
            </li>
            <li>
              <strong>Tópico:</strong> se o tópico informado não existir, ele é criado.
            </li>
            <li>
              <strong>Localização:</strong> sem latitude/longitude válidas, geramos um ponto
              aleatório na Gávea.
            </li>
            <li>
              <strong>Data:</strong> sem data, usamos o momento da importação.
            </li>
            <li>
              <strong>Urgência:</strong> valores aceitos <code>alta</code>, <code>media</code>,{" "}
              <code>baixa</code>; vazio assume <code>media</code>.
            </li>
          </ul>
          <form onSubmit={handleSeedRelatosSubmit} className="flex flex-col gap-3">
            <div className="space-y-1">
              <Label htmlFor="seed-relatos-file">Arquivo CSV</Label>
              <Input
                id="seed-relatos-file"
                ref={relatosInputRef}
                type="file"
                accept=".csv"
                onChange={(e) => setRelatosFile(e.target.files?.[0] ?? null)}
              />
            </div>
            <div>
              <Button type="submit" disabled={seedingRelatos || !relatosFile}>
                {seedingRelatos ? "Enviando..." : "Enviar CSV"}
              </Button>
            </div>
          </form>
        </section>

        <section className="rounded-md border border-gray-200 p-5">
          <h2 className="mb-1 text-base font-semibold text-gray-900">Limpar Banco de Dados</h2>
          <p className="mb-4 text-sm text-gray-500">
            Remove dados de forma permanente. Use com cautela.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button
              type="button"
              variant="destructive"
              onClick={() => setWipeScope("reports")}
            >
              Apagar relatos e encaminhamentos
            </Button>
            <Button type="button" variant="destructive" onClick={() => setWipeScope("all")}>
              Apagar tudo (incluindo tópicos)
            </Button>
          </div>
        </section>
      </div>

      <Dialog
        open={wipeScope !== null}
        onOpenChange={(o) => {
          if (!o && !wiping) setWipeScope(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar exclusão</DialogTitle>
            <DialogDescription>{wipeDescription}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setWipeScope(null)}
              disabled={wiping}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              variant="destructive"
              onClick={handleWipeConfirm}
              disabled={wiping}
            >
              {wiping ? "Apagando..." : "Confirmar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
