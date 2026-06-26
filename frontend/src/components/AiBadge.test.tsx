import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup, within } from "@testing-library/react";
import { AiBadge } from "./AiBadge";

afterEach(() => {
  cleanup();
});

describe("AiBadge", () => {
  it("exposes the accessible name 'Conteúdo gerado por IA'", () => {
    render(<AiBadge />);
    expect(screen.getByLabelText("Conteúdo gerado por IA")).toBeInTheDocument();
  });

  it("renders the visible 'IA' text", () => {
    render(<AiBadge />);
    expect(screen.getByLabelText("Conteúdo gerado por IA")).toHaveTextContent("IA");
  });

  it("carries the full tooltip in the title attribute", () => {
    render(<AiBadge />);
    expect(screen.getByLabelText("Conteúdo gerado por IA")).toHaveAttribute(
      "title",
      "Conteúdo gerado por IA — pode conter erros. Revise antes de agir.",
    );
  });

  it("marks the decorative icon as aria-hidden", () => {
    render(<AiBadge />);
    const badge = screen.getByLabelText("Conteúdo gerado por IA");
    const icon = badge.querySelector("svg");
    expect(icon).not.toBeNull();
    expect(icon).toHaveAttribute("aria-hidden", "true");
    // The icon must not contribute to the accessible name.
    expect(within(badge).queryByRole("img", { name: /sparkle/i })).toBeNull();
  });
});
