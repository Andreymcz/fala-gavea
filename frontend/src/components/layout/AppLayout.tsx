import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { Toaster } from "@/components/ui/toaster";

export function AppLayout() {
  return (
    <div className="flex h-screen flex-col bg-background overflow-hidden">
      <Header />
      <main className="flex flex-1 flex-col overflow-hidden">
        <Outlet />
      </main>
      <Toaster />
    </div>
  );
}
