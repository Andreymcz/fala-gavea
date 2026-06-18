import { useState } from "react";
import { useCreateForwarding } from "@/hooks/useForwardings";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { toast } from "@/components/ui/toast";

interface CreateForwardingDialogProps {
  open: boolean;
  selectedIds: string[];
  onSuccess: () => void;
  onClose: () => void;
}

interface FormErrors {
  institution?: string;
  proposed_solution?: string;
}

export function CreateForwardingDialog({
  open,
  selectedIds,
  onSuccess,
  onClose,
}: CreateForwardingDialogProps) {
  const { mutate: createForwarding, isPending } = useCreateForwarding();

  const [institution, setInstitution] = useState("");
  const [proposedSolution, setProposedSolution] = useState("");
  const [errors, setErrors] = useState<FormErrors>({});

  function validate(): boolean {
    const errs: FormErrors = {};
    const inst = institution.trim();
    const sol = proposedSolution.trim();
    if (inst.length < 3) errs.institution = "Nome do órgão deve ter pelo menos 3 caracteres.";
    if (inst.length > 200) errs.institution = "Nome do órgão deve ter no máximo 200 caracteres.";
    if (sol.length < 20) errs.proposed_solution = "Solução proposta deve ter pelo menos 20 caracteres.";
    if (sol.length > 5000) errs.proposed_solution = "Solução proposta deve ter no máximo 5000 caracteres.";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  function handleClose() {
    setInstitution("");
    setProposedSolution("");
    setErrors({});
    onClose();
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    createForwarding(
      {
        institution: institution.trim(),
        proposed_solution: proposedSolution.trim(),
        report_ids: selectedIds,
      },
      {
        onSuccess: (forwarding) => {
          toast(`Encaminhamento criado para ${forwarding.institution}.`, "success");
          handleClose();
          onSuccess();
        },
        onError: () => {
          toast("Erro ao criar encaminhamento. Tente novamente.", "error");
        },
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) handleClose(); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            Criar encaminhamento ({selectedIds.length} relato{selectedIds.length !== 1 ? "s" : ""})
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="institution">Órgão responsável</Label>
            <Input
              id="institution"
              value={institution}
              onChange={(e) => setInstitution(e.target.value)}
              placeholder="Ex: RioLuz, COMLURB, CET-Rio"
            />
            {errors.institution && (
              <p role="alert" className="text-xs text-red-600">{errors.institution}</p>
            )}
          </div>
          <div className="space-y-1">
            <Label htmlFor="proposed_solution">Solução proposta</Label>
            <Textarea
              id="proposed_solution"
              value={proposedSolution}
              onChange={(e) => setProposedSolution(e.target.value)}
              rows={4}
              placeholder="Descreva a solução proposta para os relatos selecionados."
            />
            {errors.proposed_solution && (
              <p role="alert" className="text-xs text-red-600">{errors.proposed_solution}</p>
            )}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Criando..." : "Confirmar"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
