import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AdminPage } from "./AdminPage";

const seedTopicos = vi.fn();
const wipeDatabase = vi.fn();

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: {
      seedTopicos: (...args: unknown[]) => seedTopicos(...args),
      wipeDatabase: (...args: unknown[]) => wipeDatabase(...args),
    },
  };
});

describe("AdminPage", () => {
  beforeEach(() => {
    seedTopicos.mockReset();
    wipeDatabase.mockReset();
  });

  it("renders both admin sections", () => {
    render(<AdminPage />);
    expect(screen.getByText("Seed de Tópicos")).toBeInTheDocument();
    expect(screen.getByText("Limpar Banco de Dados")).toBeInTheDocument();
  });

  it("uploads a CSV and calls seedTopicos", async () => {
    seedTopicos.mockResolvedValue({ inserted: 3, skipped: 1, errors: [] });
    render(<AdminPage />);

    const file = new File(["nome,descricao\nIluminação,"], "topicos.csv", { type: "text/csv" });
    const input = screen.getByLabelText(/arquivo csv/i) as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    fireEvent.click(screen.getByRole("button", { name: /enviar csv/i }));

    await waitFor(() => {
      expect(seedTopicos).toHaveBeenCalledWith(file);
    });
  });

  it("opens a confirm dialog before wiping and only wipes on confirm", async () => {
    wipeDatabase.mockResolvedValue({
      wiped: { reports: 0, forwardings: 0, report_types: 0 },
    });
    render(<AdminPage />);

    fireEvent.click(screen.getByRole("button", { name: /apagar tudo \(incluindo tópicos\)/i }));

    // Dialog appears; wipe not yet called
    expect(await screen.findByText(/confirmar exclusão/i)).toBeInTheDocument();
    expect(wipeDatabase).not.toHaveBeenCalled();

    // Confirm button in the dialog footer triggers the wipe with include_report_types=true
    fireEvent.click(screen.getByRole("button", { name: /^confirmar$/i }));

    await waitFor(() => {
      expect(wipeDatabase).toHaveBeenCalledWith(true);
    });
  });
});
