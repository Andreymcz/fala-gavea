import { useState, useCallback } from "react";

export interface Toast {
  id: string;
  message: string;
  type: "success" | "error" | "info";
}

let toastIdCounter = 0;

type ToastListener = (toasts: Toast[]) => void;
const listeners: ToastListener[] = [];
let currentToasts: Toast[] = [];

function notifyListeners() {
  listeners.forEach((l) => l([...currentToasts]));
}

export function toast(message: string, type: Toast["type"] = "info") {
  const id = String(++toastIdCounter);
  currentToasts = [...currentToasts, { id, message, type }];
  notifyListeners();
  setTimeout(() => {
    currentToasts = currentToasts.filter((t) => t.id !== id);
    notifyListeners();
  }, 3000);
}

export function useToastStore() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const subscribe = useCallback((listener: ToastListener) => {
    listeners.push(listener);
    return () => {
      const idx = listeners.indexOf(listener);
      if (idx > -1) listeners.splice(idx, 1);
    };
  }, []);
  return { toasts, setToasts, subscribe };
}
