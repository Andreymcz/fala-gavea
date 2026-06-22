import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { InlineReportDialog } from "./InlineReportDialog";

vi.mock("@/hooks/useReportTypes", () => ({
  useReportTypes: () => ({
    data: [{ id: "rt-1", name: "Iluminação pública", description: null, active: true, created_at: "2024-01-01" }],
    isLoading: false,
  }),
}));

const mockMutate = vi.fn();
vi.mock("@/hooks/useReports", () => ({
  useCreateReport: () => ({ mutate: mockMutate, isPending: false }),
}));

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient();
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("InlineReportDialog", () => {
  it("prefills lat/lon from the clicked point (shared form reuse)", () => {
    render(
      <InlineReportDialog open={true} lat={-22.97} lon={-43.22} onOpenChange={vi.fn()} />,
      { wrapper },
    );
    const latInput = screen.getByLabelText(/latitude/i) as HTMLInputElement;
    const lonInput = screen.getByLabelText(/longitude/i) as HTMLInputElement;
    expect(latInput.value).toBe("-22.970000");
    expect(lonInput.value).toBe("-43.220000");
  });

  it("shares the geolocate option from the form", () => {
    render(
      <InlineReportDialog open={true} lat={-22.97} lon={-43.22} onOpenChange={vi.fn()} />,
      { wrapper },
    );
    expect(screen.getByRole("button", { name: /usar minha localização/i })).toBeTruthy();
  });

  it("validates before submitting (shared validation)", async () => {
    render(
      <InlineReportDialog open={true} lat={-22.97} lon={-43.22} onOpenChange={vi.fn()} />,
      { wrapper },
    );
    fireEvent.click(screen.getByRole("button", { name: /registrar relato/i }));
    await waitFor(() => {
      const alerts = screen.getAllByRole("alert");
      expect(alerts.some((a) => a.textContent?.includes("pelo menos 10 caracteres"))).toBe(true);
    });
    expect(mockMutate).not.toHaveBeenCalled();
  });
});
