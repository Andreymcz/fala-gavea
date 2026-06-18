import { Button } from "@/components/ui/button";

interface SelectionBarProps {
  count: number;
  onCreateForwarding: () => void;
  onClear: () => void;
}

export function SelectionBar({ count, onCreateForwarding, onClear }: SelectionBarProps) {
  if (count === 0) return null;

  return (
    <div className="absolute bottom-8 left-1/2 z-[1000] -translate-x-1/2">
      <div className="flex items-center gap-2 rounded-full bg-white border border-gray-300 px-4 py-2 shadow-lg">
        <span className="text-sm font-medium text-gray-700">
          {count} relato{count !== 1 ? "s" : ""} selecionado{count !== 1 ? "s" : ""}
        </span>
        <Button size="sm" onClick={onCreateForwarding}>
          Criar encaminhamento ({count})
        </Button>
        <Button size="sm" variant="ghost" onClick={onClear}>
          Limpar
        </Button>
      </div>
    </div>
  );
}
