import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FiltersSidebar } from "./FiltersSidebar";

// Mock Radix Select since it needs a DOM environment to render
vi.mock("@/components/ui/select", () => ({
  Select: ({ onValueChange, value, children }: { onValueChange: (v: string) => void; value: string; children: React.ReactNode }) => (
    <select value={value} onChange={(e) => onValueChange(e.target.value)} data-testid="select">
      {children}
    </select>
  ),
  SelectTrigger: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SelectValue: ({ placeholder }: { placeholder: string }) => <option value="">{placeholder}</option>,
  SelectContent: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SelectItem: ({ value, children }: { value: string; children: React.ReactNode }) => (
    <option value={value}>{children}</option>
  ),
}));

const mockTypes = [
  { id: "type-1", name: "Iluminação pública", description: null, active: true, created_at: "2024-01-01" },
  { id: "type-2", name: "Trânsito", description: null, active: true, created_at: "2024-01-01" },
];

describe("FiltersSidebar", () => {
  it("renders filter controls", () => {
    render(
      <FiltersSidebar filters={{}} onChange={vi.fn()} reportTypes={mockTypes} />,
    );
    expect(screen.getByText("Filtros")).toBeInTheDocument();
  });

  it("calls onChange when urgency filter changes", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <FiltersSidebar filters={{}} onChange={onChange} reportTypes={mockTypes} />,
    );

    const selects = screen.getAllByTestId("select");
    // Second select is urgency (after type)
    await user.selectOptions(selects[1], "alta");

    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ urgency: "alta" }));
  });

  it("shows disabled semantic search placeholder", () => {
    render(
      <FiltersSidebar filters={{}} onChange={vi.fn()} reportTypes={mockTypes} />,
    );
    const searchInput = screen.getByPlaceholderText("Busca semântica (em breve)");
    expect(searchInput).toBeDisabled();
  });
});
