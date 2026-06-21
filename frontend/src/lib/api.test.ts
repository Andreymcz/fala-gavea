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

  it("createSavedFilter POSTs to /saved-filters with JSON body", async () => {
    const saved = { id: "sf1", name: "My Filter", body: { urgency: "alta" }, schema_ver: "1", created_at: "2024-01-01", updated_at: "2024-01-01", deprecated_fields: [] };
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 201, json: () => Promise.resolve(saved) });
    vi.stubGlobal("fetch", mockFetch);
    localStorage.setItem("fala_gavea_token", "tok");

    const result = await api.createSavedFilter({ name: "My Filter", body: { urgency: "alta" } });

    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/saved-filters");
    expect(init.method).toBe("POST");
    expect(init.headers["Authorization"]).toBe("Bearer tok");
    expect(JSON.parse(init.body as string)).toEqual({ name: "My Filter", body: { urgency: "alta" } });
    expect(result).toEqual(saved);
  });

  it("listSavedFilters GETs /saved-filters", async () => {
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: () => Promise.resolve([]) });
    vi.stubGlobal("fetch", mockFetch);
    localStorage.setItem("fala_gavea_token", "tok");

    const result = await api.listSavedFilters();

    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/saved-filters");
    expect(init.method).toBe("GET");
    expect(result).toEqual([]);
  });

  it("getSavedFilter GETs /saved-filters/:id", async () => {
    const saved = { id: "sf1", name: "F", body: {}, schema_ver: "1", created_at: "2024-01-01", updated_at: "2024-01-01", deprecated_fields: [] };
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: () => Promise.resolve(saved) });
    vi.stubGlobal("fetch", mockFetch);

    await api.getSavedFilter("sf1");

    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain("/saved-filters/sf1");
  });

  it("updateSavedFilter PATCHes /saved-filters/:id with JSON body", async () => {
    const saved = { id: "sf1", name: "Updated", body: {}, schema_ver: "1", created_at: "2024-01-01", updated_at: "2024-01-02", deprecated_fields: [] };
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: () => Promise.resolve(saved) });
    vi.stubGlobal("fetch", mockFetch);

    await api.updateSavedFilter("sf1", { name: "Updated" });

    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/saved-filters/sf1");
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(init.body as string)).toEqual({ name: "Updated" });
  });

  it("deleteSavedFilter DELETEs /saved-filters/:id and resolves void on 204", async () => {
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 204, json: () => Promise.resolve(null) });
    vi.stubGlobal("fetch", mockFetch);

    const result = await api.deleteSavedFilter("sf1");

    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/saved-filters/sf1");
    expect(init.method).toBe("DELETE");
    expect(result).toBeUndefined();
  });

  it("queryReports POSTs to /reports/query with JSON body", async () => {
    const mockResponse = {
      items: [],
      total: 0,
      limit: 200,
      offset: 0,
      ranked_by: "relevance",
    };
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockResponse),
    });
    vi.stubGlobal("fetch", mockFetch);

    const body = { urgencies: ["alta"], limit: 200 };
    const result = await api.queryReports(body);

    expect(mockFetch).toHaveBeenCalledOnce();
    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/reports/query");
    expect(init.method).toBe("POST");
    expect(init.headers["Content-Type"]).toBe("application/json");
    expect(JSON.parse(init.body as string)).toEqual(body);
    expect(result).toEqual(mockResponse);
  });
});
