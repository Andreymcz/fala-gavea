import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/toast";
import { useWorkspaceStore } from "@/store/workspaceStore";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { HelpChat } from "@/features/help/HelpChat";
import { AiBadge } from "@/components/AiBadge";

export function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const basketCount = useWorkspaceStore((s) => s.selectedIds.size);
  const showView = useWorkspaceStore((s) => s.showView);
  const [helpOpen, setHelpOpen] = useState(false);

  const isAgent = user?.role === "agent" || user?.role === "admin";

  function handleLogout() {
    logout();
    toast("Saiu com sucesso.", "success");
    navigate("/");
  }

  function handleOpenBasket() {
    showView("cesta");
    navigate("/");
  }

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white">
      <div className="mx-auto flex h-14 max-w-screen-xl items-center justify-between px-4">
        <Link to="/" className="text-lg font-bold text-blue-700 hover:text-blue-800">
          Fala Gávea
        </Link>
        <nav className="flex items-center gap-3">
          <Link
            to="/"
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Mapa
          </Link>
          {user && (
            <Link
              to="/report"
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Novo relato
            </Link>
          )}
          {user && (
            <Link
              to="/?meus_relatos=1"
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Meus relatos
            </Link>
          )}
          <Link
            to="/encaminhamentos"
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Encaminhamentos
          </Link>
          {user && (user.role === "agent" || user.role === "admin") && (
            <Link
              to="/agent"
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Gerenciar encaminhamentos
            </Link>
          )}
          {user?.role === "admin" && (
            <Link
              to="/admin"
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Painel admin
            </Link>
          )}
          {user && (
            <button
              type="button"
              onClick={() => setHelpOpen(true)}
              className="text-sm text-gray-600 hover:text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded"
            >
              Ajuda
            </button>
          )}
          {isAgent && (
            <button
              type="button"
              onClick={handleOpenBasket}
              aria-label={`Cesta de relatos (${basketCount})`}
              className="relative flex items-center rounded-md px-2 py-1 text-sm text-gray-600 hover:bg-gray-100 hover:text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            >
              Cesta
              {basketCount > 0 && (
                <span className="ml-1 inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-blue-600 px-1.5 text-xs font-semibold text-white">
                  {basketCount}
                </span>
              )}
            </button>
          )}
          {!user ? (
            <Link to="/login">
              <Button size="sm">Entrar</Button>
            </Link>
          ) : (
            <Button size="sm" variant="outline" onClick={handleLogout}>
              Sair ({user.name})
            </Button>
          )}
        </nav>
      </div>

      {user && (
        <Dialog open={helpOpen} onOpenChange={setHelpOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                Ajuda da plataforma
                <AiBadge size="xs" />
              </DialogTitle>
              <DialogDescription>
                Assistente sobre como usar o Fala-Gávea. Não é o assistente de exploração de
                relatos.
              </DialogDescription>
            </DialogHeader>
            <HelpChat />
          </DialogContent>
        </Dialog>
      )}
    </header>
  );
}
