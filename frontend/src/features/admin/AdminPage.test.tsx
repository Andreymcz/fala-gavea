import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AdminPage } from "./AdminPage";

const seedTopicos = vi.fn();
const seedRelatosStream = vi.fn();
const wipeDatabase = vi.fn();

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: {
      seedTopicos: (...args: unknown[]) => seedTopicos(...args),
      seedRelatosStream: (...args: unknown[]) => seedRelatosStream(...args),
      wipeDatabase: (...args: unknown[]) => wipeDatabase(...args),
    },
  };
});

describe("AdminPage", () => {
  beforeEach(() => {
    seedTopicos.mockReset();
    seedRelatosStream.mockReset();
    wipeDatabase.mockReset();
  });

  it("renders all admin sections", () => {
    render(<AdminPage />);
    expect(screen.getByText("Seed de Tópicos")).toBeInTheDocument();
    expect(screen.getByText("Seed de Relatos")).toBeInTheDocument();
    expect(screen.getByText("Limpar Banco de Dados")).toBeInTheDocument();
  });

  it("uploads a CSV and calls seedTopicos", async () => {
    seedTopicos.mockResolvedValue({ inserted: 3, skipped: 1, errors: [] });
    render(<AdminPage />);

    const file = new File(["nome,descricao\nIluminação,"], "topicos.csv", { type: "text/csv" });
    // The first "Arquivo CSV" input belongs to the Seed de Tópicos section.
    const input = screen.getAllByLabelText(/arquivo csv/i)[0] as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    fireEvent.click(screen.getAllByRole("button", { name: /enviar csv/i })[0]);

    await waitFor(() => {
      expect(seedTopicos).toHaveBeenCalledWith(file);
    });
  });

  it("uploads a CSV and streams seedRelatos progress", async () => {
    seedRelatosStream.mockImplementation(
      (_file: File, onProgress: (p: { processed: number; total: number }) => void) => {
        onProgress({ processed: 1, total: 1 });
        return Promise.resolve({ inserted: 5, skipped: 0, errors: [] });
      },
    );
    render(<AdminPage />);

    const file = new File(
      ["user_id,texto_relato,topico\nu1,Buraco na rua,Iluminacao"],
      "relatos.csv",
      { type: "text/csv" },
    );
    // The second "Arquivo CSV" input belongs to the Seed de Relatos section.
    const input = screen.getAllByLabelText(/arquivo csv/i)[1] as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    fireEvent.click(screen.getAllByRole("button", { name: /enviar csv/i })[1]);

    await waitFor(() => {
      expect(seedRelatosStream).toHaveBeenCalledWith(file, expect.any(Function));
    });
    expect(seedTopicos).not.toHaveBeenCalled();
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
