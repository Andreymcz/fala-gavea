import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ReportFeature, PublicForwarding } from "@/lib/types";
import { ReportPopup } from "./ReportPopup";

let mockForwardings: PublicForwarding[] = [];
vi.mock("@/hooks/useForwardings", () => ({
  useReportForwardings: () => ({ data: mockForwardings, isLoading: false }),
}));

function makeFeature(): ReportFeature {
  return {
    type: "Feature",
    geometry: { type: "Point", coordinates: [-43.22, -22.97] },
    properties: {
      id: "r-1",
      text: "Poste apagado",
      urgency: "alta",
      status: "encaminhado",
      report_type_id: "type-1",
      author_id: "u-1",
      photo_url: null,
      created_at: "2026-06-01T10:00:00Z",
    },
  };
}

const typeMap = new Map([["type-1", "Iluminação"]]);

describe("ReportPopup — linked encaminhamento badge", () => {
  it("shows the badge when the report has linked forwardings", () => {
    mockForwardings = [
      {
        id: "fwd-1",
        institution: "RioLuz",
        proposed_solution: "x".repeat(30),
        status: "solucao_em_andamento",
        reports: [],
        created_at: "2026-06-01T10:00:00Z",
        updated_at: "2026-06-01T10:00:00Z",
      },
    ];
    render(<ReportPopup feature={makeFeature()} typeMap={typeMap} />);
    expect(screen.getByText(/Encaminhado → RioLuz · em andamento/i)).toBeTruthy();
  });

  it("renders no badge when there are no linked forwardings", () => {
    mockForwardings = [];
    render(<ReportPopup feature={makeFeature()} typeMap={typeMap} />);
    expect(screen.queryByText(/Encaminhado →/i)).toBeNull();
  });
});
