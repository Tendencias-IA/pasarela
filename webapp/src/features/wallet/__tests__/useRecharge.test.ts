import { act, renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse, delay } from "msw";
import { describe, expect, it, vi } from "vitest";

import { setSessionExpiredHandler } from "../../../shared/api/client";
import { server } from "../../../test/server";
import { FORMAT_MESSAGE, RANGE_MESSAGE, useRecharge } from "../useRecharge";

const URL = "/api/v1/wallet/recharges";

function okResponse(amount: string, balance: string) {
  return HttpResponse.json(
    {
      id: 1,
      type: "recarga",
      status: "exitosa",
      amount,
      balance_after: balance,
      created_at: "2026-10-14T21:40:00Z",
    },
    { status: 201 },
  );
}

function problem(
  status: number,
  code: string,
  detail: string,
  errors?: { field: string; message: string }[],
) {
  return HttpResponse.json({ type: "t", title: code, status, code, detail, errors }, { status });
}

describe("useRecharge (HU-08)", () => {
  it("envía el monto canónico con Idempotency-Key y expone el resultado (CA-3)", async () => {
    const seen: { headers: Headers; body: unknown }[] = [];
    server.use(
      http.post(URL, async ({ request }) => {
        const body: unknown = await request.json();
        seen.push({ headers: request.headers, body });
        return okResponse("50000.00", "70000.00");
      }),
    );
    const { result } = renderHook(() => useRecharge());

    act(() => {
      result.current.setAmount("50.000");
    });
    await act(() => result.current.submit());

    expect(result.current.state).toMatchObject({
      kind: "success",
      result: { balance_after: "70000.00" },
    });
    expect(seen[0]?.body).toEqual({ amount: "50000.00" });
    expect(seen[0]?.headers.get("Idempotency-Key")).toMatch(/^[0-9a-f-]{36}$/);
    expect(seen[0]?.headers.get("X-Requested-With")).toBe("fetch");
  });

  it("rechaza en cliente montos fuera de rango y no numéricos sin llamar a la API (CA-2)", async () => {
    const spy = vi.fn();
    server.use(http.post(URL, spy));
    const { result } = renderHook(() => useRecharge());

    act(() => {
      result.current.setAmount("4999");
    });
    await act(() => result.current.submit());
    expect(result.current.fieldError).toBe(RANGE_MESSAGE);

    act(() => {
      result.current.setAmount("abc");
    });
    await act(() => result.current.submit());
    expect(result.current.fieldError).toBe(FORMAT_MESSAGE);

    expect(spy).not.toHaveBeenCalled();
    expect(result.current.state.kind).toBe("idle");
  });

  it("mapea el error de campo del problem 422 al campo (CA-5, CA-9)", async () => {
    server.use(
      http.post(URL, () =>
        problem(422, "amount_out_of_range", "Fuera de rango.", [
          { field: "amount", message: "Debe estar entre 5000.00 y 5000000.00" },
        ]),
      ),
    );
    const { result } = renderHook(() => useRecharge());

    act(() => {
      result.current.setAmount("50000");
    });
    await act(() => result.current.submit());

    expect(result.current.fieldError).toBe("Debe estar entre 5000.00 y 5000000.00");
    expect(result.current.state).toEqual({ kind: "rejected", message: "Fuera de rango." });
  });

  it("expone el detalle cuando la API rechaza sin error de campo", async () => {
    server.use(http.post(URL, () => problem(404, "wallet_not_found", "Sin billetera.")));
    const { result } = renderHook(() => useRecharge());

    act(() => {
      result.current.setAmount("50000");
    });
    await act(() => result.current.submit());

    expect(result.current.fieldError).toBeNull();
    expect(result.current.state).toEqual({ kind: "rejected", message: "Sin billetera." });
  });

  it("informa falta de conexión cuando la respuesta no es un problem", async () => {
    server.use(http.post(URL, () => HttpResponse.text("gateway timeout", { status: 504 })));
    const { result } = renderHook(() => useRecharge());

    act(() => {
      result.current.setAmount("50000");
    });
    await act(() => result.current.submit());

    expect(result.current.state).toMatchObject({ kind: "rejected" });
  });

  it("reutiliza la misma clave en un doble envío y bloquea mientras está en vuelo (FR-011)", async () => {
    const keys: string[] = [];
    server.use(
      http.post(URL, async ({ request }) => {
        keys.push(request.headers.get("Idempotency-Key") ?? "");
        await delay(100);
        return okResponse("50000.00", "50000.00");
      }),
    );
    const { result } = renderHook(() => useRecharge());

    act(() => {
      result.current.setAmount("50000");
    });
    let first: Promise<void> = Promise.resolve();
    act(() => {
      first = result.current.submit();
    });
    expect(result.current.state.kind).toBe("submitting");
    await act(() => result.current.submit());
    await act(() => first);

    expect(keys).toHaveLength(1);
    expect(result.current.state.kind).toBe("success");
  });

  it("dos llamadas en el mismo tick (Enter + clic) envían una sola petición", async () => {
    let requests = 0;
    server.use(
      http.post(URL, async () => {
        requests += 1;
        await delay(50);
        return okResponse("50000.00", "50000.00");
      }),
    );
    const { result } = renderHook(() => useRecharge());

    act(() => {
      result.current.setAmount("50000");
    });
    // Sin re-render entre ambas: la guarda no puede depender del estado capturado.
    await act(() => Promise.all([result.current.submit(), result.current.submit()]));

    expect(requests).toBe(1);
    expect(result.current.state.kind).toBe("success");
  });

  it("genera una clave distinta cuando cambia el monto", async () => {
    const keys: string[] = [];
    server.use(
      http.post(URL, ({ request }) => {
        keys.push(request.headers.get("Idempotency-Key") ?? "");
        return problem(404, "wallet_not_found", "x");
      }),
    );
    const { result } = renderHook(() => useRecharge());

    act(() => {
      result.current.setAmount("50000");
    });
    await act(() => result.current.submit());
    act(() => {
      result.current.setAmount("60000");
    });
    await act(() => result.current.submit());

    expect(keys).toHaveLength(2);
    expect(keys[0]).not.toBe(keys[1]);
  });

  it("invoca el manejador de sesión expirada ante 401 invalid_session (HU-04 CA-2)", async () => {
    const handler = vi.fn();
    setSessionExpiredHandler(handler);
    server.use(http.post(URL, () => problem(401, "invalid_session", "Sesión vencida.")));
    const { result } = renderHook(() => useRecharge());

    act(() => {
      result.current.setAmount("50000");
    });
    await act(() => result.current.submit());

    await waitFor(() => {
      expect(handler).toHaveBeenCalledOnce();
    });
    expect(result.current.state.kind).toBe("rejected");
  });

  it("reset vuelve al estado inicial con una clave nueva", async () => {
    const keys: string[] = [];
    server.use(
      http.post(URL, ({ request }) => {
        keys.push(request.headers.get("Idempotency-Key") ?? "");
        return okResponse("50000.00", "50000.00");
      }),
    );
    const { result } = renderHook(() => useRecharge());
    act(() => {
      result.current.setAmount("50000");
    });
    await act(() => result.current.submit());

    act(() => {
      result.current.reset();
    });
    act(() => {
      result.current.setAmount("50000");
    });
    await act(() => result.current.submit());

    expect(result.current.amount).toBe("50000");
    expect(keys[0]).not.toBe(keys[1]);
  });
});
