import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AuthProvider, useAuth } from "./AuthContext";
import type { User } from "@/lib/types";

vi.mock("@/lib/api", () => ({
  api: {
    me: vi.fn(),
    login: vi.fn(),
  },
}));

import { api } from "@/lib/api";

const mockUser: User = {
  id: "1",
  email: "agent@gavea.br",
  name: "Agent",
  role: "agent",
  created_at: "2024-01-01",
};

function TestConsumer() {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div>loading</div>;
  if (!user) return <div>no user</div>;
  return <div>{user.name}</div>;
}

beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("AuthContext", () => {
  it("hydrates user from token on mount", async () => {
    localStorage.setItem("fala_gavea_token", "valid-token");
    vi.mocked(api.me).mockResolvedValue(mockUser);

    render(
      <MemoryRouter>
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Agent")).toBeInTheDocument();
    });
  });

  it("logs out when me() rejects", async () => {
    localStorage.setItem("fala_gavea_token", "bad-token");
    vi.mocked(api.me).mockRejectedValue(new Error("401"));

    render(
      <MemoryRouter>
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("no user")).toBeInTheDocument();
    });
    expect(localStorage.getItem("fala_gavea_token")).toBeNull();
  });

  it("logs out when auth:unauthorized event fires", async () => {
    localStorage.setItem("fala_gavea_token", "valid-token");
    vi.mocked(api.me).mockResolvedValue(mockUser);

    render(
      <MemoryRouter>
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText("Agent")).toBeInTheDocument());

    act(() => {
      window.dispatchEvent(new Event("auth:unauthorized"));
    });

    await waitFor(() => {
      expect(screen.getByText("no user")).toBeInTheDocument();
    });
    expect(localStorage.getItem("fala_gavea_token")).toBeNull();
  });
});
