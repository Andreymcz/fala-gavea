import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { PublicForwarding } from "@/lib/types";

vi.mock("@/auth/AuthContext", () => ({
  useAuth: () => ({ user: null, token: null }),
}));

const getPublicForwardings = vi.fn();
vi.mock("@/lib/api", () => ({
  api: {
    getPublicForwardings: (...args: unknown[]) => getPublicForwardings(...args),
  },
}));

import { PublicForwardingsPage } from "./PublicForwardingsPage";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

const sample: PublicForwarding = {
  id: "fwd-1",
  institution: "RioLuz",
  proposed_solution: "Troca de lâmpadas em toda a quadra afetada pela falta de iluminação.",
  status: "solucao_em_andamento",
  reports: [
    { id: "r-1", text: "Poste apagado na esquina", urgency: "alta", status: "encaminhado" },
  ],
  created_at: "2026-06-01T10:00:00Z",
  updated_at: "2026-06-02T10:00:00Z",
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("PublicForwardingsPage", () => {
  it("renders forwardings from the PUBLIC endpoint without login", async () => {
    getPublicForwardings.mockResolvedValue([sample]);
    render(<PublicForwardingsPage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText("RioLuz")).toBeTruthy();
    });
    // Consumes the public list endpoint, not the agent one.
    expect(getPublicForwardings).toHaveBeenCalled();
    // Status label visible.
    expect(screen.getByText(/em andamento/i)).toBeTruthy();
  });

  it("shows the empty state when there are no forwardings", async () => {
    getPublicForwardings.mockResolvedValue([]);
    render(<PublicForwardingsPage />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText(/nenhum encaminhamento/i)).toBeTruthy();
    });
  });
});
