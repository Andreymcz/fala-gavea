import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { ReportFormPage } from "./ReportFormPage";

vi.mock("@/hooks/useReportTypes", () => ({
  useReportTypes: () => ({
    data: [
      { id: "rt-1", name: "Iluminação pública", description: null, active: true, created_at: "2024-01-01" },
    ],
    isLoading: false,
  }),
}));

vi.mock("@/hooks/useReports", () => ({
  useCreateReport: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  useReports: vi.fn(() => ({ data: undefined, isLoading: false })),
}));

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient();
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("ReportFormPage", () => {
  it("shows validation error when text is too short", async () => {
    render(<ReportFormPage />, { wrapper });

    const textarea = screen.getByLabelText(/descrição do problema/i);
    const submit = screen.getByRole("button", { name: /registrar relato/i });

    fireEvent.change(textarea, { target: { value: "curto" } });
    fireEvent.click(submit);

    await waitFor(() => {
      const alerts = screen.getAllByRole("alert");
      expect(alerts.some((a) => a.textContent?.includes("pelo menos 10 caracteres"))).toBe(true);
    });
  });

  it("fills lat/lon when geolocation succeeds", async () => {
    const mockGeolocation = {
      getCurrentPosition: vi.fn((success) =>
        success({ coords: { latitude: -22.9731, longitude: -43.2272 } }),
      ),
    };
    Object.defineProperty(navigator, "geolocation", {
      value: mockGeolocation,
      configurable: true,
    });

    render(<ReportFormPage />, { wrapper });

    const geoButton = screen.getByRole("button", { name: /usar minha localização/i });
    fireEvent.click(geoButton);

    await waitFor(() => {
      const latInput = screen.getByLabelText(/latitude/i) as HTMLInputElement;
      expect(latInput.value).toContain("-22.97");
    });
  });
});
