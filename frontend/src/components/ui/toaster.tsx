import { useEffect } from "react";
import { useToastStore, type Toast } from "./toast";
import { cn } from "@/lib/utils";

function ToastItem({ toast }: { toast: Toast }) {
  return (
    <div
      className={cn(
        "pointer-events-auto flex w-full max-w-sm items-center gap-3 rounded-lg border px-4 py-3 shadow-lg",
        toast.type === "success" && "border-green-200 bg-green-50 text-green-800",
        toast.type === "error" && "border-red-200 bg-red-50 text-red-800",
        toast.type === "info" && "border-blue-200 bg-blue-50 text-blue-800",
      )}
      role="alert"
    >
      <span className="text-sm font-medium">{toast.message}</span>
    </div>
  );
}

export function Toaster() {
  const { toasts, setToasts, subscribe } = useToastStore();

  useEffect(() => {
    const unsubscribe = subscribe(setToasts);
    return unsubscribe;
  }, [subscribe, setToasts]);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} />
      ))}
    </div>
  );
}
