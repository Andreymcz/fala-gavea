import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { HelpChat } from "./HelpChat";
import type { User } from "@/lib/types";

const postHelpChat = vi.fn();

vi.mock("@/api/helpChat", () => ({
  postHelpChat: (...args: unknown[]) => postHelpChat(...args),
}));

const mockUser: User = {
  id: "1",
  email: "citizen@gavea.br",
  name: "Cidadão",
  role: "citizen",
  created_at: "2024-01-01",
};

let authValue: { user: User | null; token: string | null } = {
  user: mockUser,
  token: "jwt-token",
};

vi.mock("@/auth/AuthContext", () => ({
  useAuth: () => authValue,
}));

describe("HelpChat", () => {
  beforeEach(() => {
    postHelpChat.mockReset();
    authValue = { user: mockUser, token: "jwt-token" };
  });

  it("renders the answer and the 'Fontes' citations from postHelpChat", async () => {
    postHelpChat.mockResolvedValue({
      response: "Para registrar um relato, clique em Novo relato.",
      cited_docs: [
        { source_path: "product-design/project/standards.md", section_title: "Relatos", score: 0.9 },
        { source_path: "_output/plans/plan-000100.md", section_title: "", score: 0.5 },
      ],
    });

    render(<HelpChat />);

    const input = screen.getByLabelText(/pergunta sobre a plataforma/i);
    fireEvent.change(input, { target: { value: "Como registro um relato?" } });
    fireEvent.click(screen.getByRole("button", { name: /perguntar/i }));

    await waitFor(() => {
      expect(postHelpChat).toHaveBeenCalledWith("Como registro um relato?", "jwt-token");
    });

    expect(
      await screen.findByText("Para registrar um relato, clique em Novo relato."),
    ).toBeInTheDocument();

    // "Fontes" header + the cited docs rendered as display-only text (source_path[#section_title]).
    expect(screen.getByText(/fontes/i)).toBeInTheDocument();
    expect(
      screen.getByText("product-design/project/standards.md#Relatos"),
    ).toBeInTheDocument();
    // Empty section_title -> no trailing "#".
    expect(screen.getByText("_output/plans/plan-000100.md")).toBeInTheDocument();
  });

  it("shows a graceful pt-BR message when the assistant is unavailable", async () => {
    postHelpChat.mockRejectedValue(new Error("unavailable"));

    render(<HelpChat />);

    fireEvent.change(screen.getByLabelText(/pergunta sobre a plataforma/i), {
      target: { value: "oi" },
    });
    fireEvent.click(screen.getByRole("button", { name: /perguntar/i }));

    expect(await screen.findByText(/indisponível no momento/i)).toBeInTheDocument();
  });

  it("renders nothing for unauthenticated users", () => {
    authValue = { user: null, token: null };
    const { container } = render(<HelpChat />);
    expect(container).toBeEmptyDOMElement();
  });
});
