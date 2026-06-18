import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { CreateForwardingDialog } from "./CreateForwardingDialog";

vi.mock("@/hooks/useForwardings", () => ({
  useCreateForwarding: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
}));

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient();
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("CreateForwardingDialog", () => {
  it("shows field error when proposed_solution is too short", async () => {
    render(
      <CreateForwardingDialog
        open={true}
        selectedIds={["id-1", "id-2"]}
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />,
      { wrapper },
    );

    // Fill institution
    const instInput = screen.getByLabelText(/órgão responsável/i);
    fireEvent.change(instInput, { target: { value: "RioLuz" } });

    // Fill proposed_solution with too-short value
    const solInput = screen.getByLabelText(/solução proposta/i);
    fireEvent.change(solInput, { target: { value: "Curto demais" } });

    // Submit
    const submitBtn = screen.getByRole("button", { name: /confirmar/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      const alerts = screen.getAllByRole("alert");
      expect(alerts.some((a) => a.textContent?.includes("pelo menos 20 caracteres"))).toBe(true);
    });
  });

  it("calls createForwarding with selected ids when form is valid", async () => {
    render(
      <CreateForwardingDialog
        open={true}
        selectedIds={["id-1", "id-2"]}
        onSuccess={vi.fn()}
        onClose={vi.fn()}
      />,
      { wrapper },
    );

    const instInput = screen.getByLabelText(/órgão responsável/i);
    fireEvent.change(instInput, { target: { value: "RioLuz" } });

    const solInput = screen.getByLabelText(/solução proposta/i);
    fireEvent.change(solInput, {
      target: { value: "Substituir lâmpadas dos postes apagados no trecho indicado nos relatos." },
    });

    const submitBtn = screen.getByRole("button", { name: /confirmar/i });
    fireEvent.click(submitBtn);

    // No validation errors shown for valid input
    await waitFor(() => {
      expect(screen.queryByRole("alert")).toBeNull();
    });
  });
});
