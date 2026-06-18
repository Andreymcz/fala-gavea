import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { StatusSelect } from "./StatusSelect";

vi.mock("@/hooks/useForwardings", () => ({
  useUpdateForwardingStatus: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
  useCreateForwarding: () => ({ mutate: vi.fn(), isPending: false }),
  useForwardings: () => ({ data: [], isLoading: false }),
}));

vi.mock("@/components/ui/select", () => ({
  Select: ({
    onValueChange,
    value,
    children,
    disabled,
  }: {
    onValueChange: (v: string) => void;
    value: string;
    children: React.ReactNode;
    disabled?: boolean;
  }) => (
    <select
      value={value}
      onChange={(e) => onValueChange(e.target.value)}
      disabled={disabled}
      data-testid="status-select"
    >
      {children}
    </select>
  ),
  SelectTrigger: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SelectValue: () => null,
  SelectContent: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SelectItem: ({ value, children }: { value: string; children: React.ReactNode }) => (
    <option value={value}>{children}</option>
  ),
}));

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient();
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("StatusSelect", () => {
  it("renders with current status selected", () => {
    render(
      <StatusSelect forwardingId="fwd-1" currentStatus="aguardando_solucao" />,
      { wrapper },
    );
    const select = screen.getByTestId("status-select") as HTMLSelectElement;
    expect(select.value).toBe("aguardando_solucao");
  });

  it("renders all three status options", () => {
    render(
      <StatusSelect forwardingId="fwd-1" currentStatus="aguardando_solucao" />,
      { wrapper },
    );
    expect(screen.getByText("Aguardando solução")).toBeInTheDocument();
    expect(screen.getByText("Solução em andamento")).toBeInTheDocument();
    expect(screen.getByText("Finalizado")).toBeInTheDocument();
  });
});
