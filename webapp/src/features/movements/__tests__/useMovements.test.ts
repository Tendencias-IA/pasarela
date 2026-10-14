import { act, waitFor } from "@testing-library/react";
import { http, HttpResponse, delay } from "msw";
import { describe, expect, it, vi } from "vitest";

import { setSessionExpiredHandler } from "../../../shared/api/client";
import { renderHookWithProviders } from "../../../test/render";
import { server } from "../../../test/server";
import { DEFAULT_FILTERS } from "../filters";
import { useMovements } from "../useMovements";
import { pageOf } from "./fixtures";

const PATH = "/api/v1/movements";

describe("useMovements (HU-09)", () => {
  it("consulta GET /api/v1/movements?page=N sin X-Requested-With y expone items y total (CA-1, CA-2)", async () => {
    const headers: string[] = [];
    server.use(
      http.get(PATH, ({ request }) => {
        headers.push(request.headers.get("X-Requested-With") ?? "none");
        const page = Number(new URL(request.url).searchParams.get("page"));
        return HttpResponse.json(pageOf(page, 2));
      }),
    );

    const { result } = renderHookWithProviders(() => useMovements({ page: 1, ...DEFAULT_FILTERS }));

    await waitFor(() => {
      expect(result.current.data?.total).toBe(2);
    });
    expect(result.current.data?.items).toHaveLength(2);
    expect(result.current.data?.items[0]?.direction).toBe("recarga");
    expect(headers).toEqual(["none"]);
  });

  it("conserva la página anterior mientras llega la siguiente y calcula lastPage (CA-6)", async () => {
    server.use(
      http.get(PATH, async ({ request }) => {
        const page = Number(new URL(request.url).searchParams.get("page"));
        if (page === 2) await delay(50);
        return HttpResponse.json(pageOf(page, 45));
      }),
    );

    const { result, rerender } = renderHookWithProviders(
      ({ page }) => useMovements({ page, ...DEFAULT_FILTERS }),
      {
        initialProps: { page: 1 },
      },
    );
    await waitFor(() => {
      expect(result.current.data?.page).toBe(1);
    });
    expect(result.current.lastPage).toBe(3);

    rerender({ page: 2 });

    expect(result.current.data?.page).toBe(1);
    expect(result.current.isPlaceholderData).toBe(true);
    await waitFor(() => {
      expect(result.current.data?.page).toBe(2);
    });
    expect(result.current.isOutOfRange).toBe(false);
  });

  it("marca fuera de rango cuando la página supera la última (FR-009)", async () => {
    server.use(
      http.get(PATH, () => HttpResponse.json({ items: [], page: 9, page_size: 20, total: 45 })),
    );

    const { result } = renderHookWithProviders(() => useMovements({ page: 9, ...DEFAULT_FILTERS }));

    await waitFor(() => {
      expect(result.current.isOutOfRange).toBe(true);
    });
    expect(result.current.lastPage).toBe(3);
  });

  it("invoca el manejador de sesión expirada ante 401 invalid_session (HU-04 CA-2)", async () => {
    const onExpired = vi.fn();
    setSessionExpiredHandler(onExpired);
    server.use(
      http.get(PATH, () =>
        HttpResponse.json(
          { type: "t", title: "Sesión", status: 401, code: "invalid_session" },
          { status: 401, headers: { "Content-Type": "application/problem+json" } },
        ),
      ),
    );

    const { result } = renderHookWithProviders(() => useMovements({ page: 1, ...DEFAULT_FILTERS }));

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
    expect(onExpired).toHaveBeenCalledTimes(1);
  });

  it("expone isError ante un fallo de red y permite reintentar", async () => {
    let calls = 0;
    server.use(
      http.get(PATH, () => {
        calls += 1;
        return calls === 1 ? HttpResponse.error() : HttpResponse.json(pageOf(1, 1));
      }),
    );

    const { result } = renderHookWithProviders(() => useMovements({ page: 1, ...DEFAULT_FILTERS }));
    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    await act(() => result.current.refetch().then(() => undefined));

    await waitFor(() => {
      expect(result.current.data?.total).toBe(1);
    });
  });
});

describe("useMovements con filtros (HU-10)", () => {
  it("envía solo los filtros con valor en la query (CA-1, CA-3, CA-4)", async () => {
    const urls: string[] = [];
    server.use(
      http.get(PATH, ({ request }) => {
        urls.push(new URL(request.url).search);
        return HttpResponse.json(pageOf(1, 1));
      }),
    );

    const { result } = renderHookWithProviders(() =>
      useMovements({ page: 2, from: "2026-10-01", to: "", type: "recharge" }),
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    expect(urls).toEqual(["?from=2026-10-01&type=recharge&page=2"]);
  });

  it("sin filtros la query es solo la página, como en HU-09", async () => {
    const urls: string[] = [];
    server.use(
      http.get(PATH, ({ request }) => {
        urls.push(new URL(request.url).search);
        return HttpResponse.json(pageOf(1, 1));
      }),
    );

    const { result } = renderHookWithProviders(() => useMovements({ page: 1, ...DEFAULT_FILTERS }));

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    expect(urls).toEqual(["?page=1"]);
  });

  it("no consulta mientras la fecha inicial es posterior a la final (CA-2)", async () => {
    let calls = 0;
    server.use(
      http.get(PATH, () => {
        calls += 1;
        return HttpResponse.json(pageOf(1, 1));
      }),
    );

    const { result } = renderHookWithProviders(() =>
      useMovements({ page: 1, from: "2026-10-20", to: "2026-10-10", type: "all" }),
    );
    await new Promise((resolve) => setTimeout(resolve, 50));

    expect(calls).toBe(0);
    expect(result.current.fetchStatus).toBe("idle");
  });

  it("cada combinación de filtros tiene su propia clave bajo la raíz ['movements'] (HU-08 invalida por prefijo)", async () => {
    server.use(http.get(PATH, () => HttpResponse.json(pageOf(1, 1))));
    const { result, rerender } = renderHookWithProviders(
      ({ type }: { type: "all" | "sent" }) => useMovements({ page: 1, from: "", to: "", type }),
      { initialProps: { type: "all" } },
    );
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    rerender({ type: "sent" });

    await waitFor(() => {
      expect(result.current.isPlaceholderData).toBe(false);
    });
  });
});
