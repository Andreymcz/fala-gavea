import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/toast";

export function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    toast("Saiu com sucesso.", "success");
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
          {user && (user.role === "agent" || user.role === "admin") && (
            <Link
              to="/agent"
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Encaminhamentos
            </Link>
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
    </header>
  );
}
