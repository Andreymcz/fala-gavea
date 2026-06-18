import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { api, ApiError } from "./api";

describe("api client", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("login sends urlencoded body with username and password", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ access_token: "tok123" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    await api.login("user@test.com", "pass123");

    expect(mockFetch).toHaveBeenCalledOnce();
    const [_url, init] = mockFetch.mock.calls[0];
    expect(init.headers["Content-Type"]).toBe("application/x-www-form-urlencoded");
    const body = init.body as URLSearchParams;
    expect(body.get("username")).toBe("user@test.com");
    expect(body.get("password")).toBe("pass123");
  });

  it("dispatches auth:unauthorized event on 401 and throws ApiError", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: "Not authenticated" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const eventFired = new Promise<void>((resolve) => {
      window.addEventListener("auth:unauthorized", () => resolve(), { once: true });
    });

    await expect(api.me()).rejects.toThrow(ApiError);

    await eventFired;
  });

  it("throws ApiError with status and detail on non-401 error", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: () => Promise.resolve({ detail: "Validation error" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    await expect(api.getReportTypes()).rejects.toThrow(ApiError);
    try {
      await api.getReportTypes();
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      if (e instanceof ApiError) {
        expect(e.status).toBe(422);
        expect(e.detail).toBe("Validation error");
      }
    }
  });

  it("attaches Bearer token from localStorage when present", async () => {
    localStorage.setItem("fala_gavea_token", "my-token");
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ id: "1", email: "a@b.com", name: "A", role: "citizen", created_at: "2024-01-01" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    await api.me();

    const [_url, init] = mockFetch.mock.calls[0];
    expect(init.headers["Authorization"]).toBe("Bearer my-token");
  });
});
