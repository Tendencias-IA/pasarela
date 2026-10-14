import { act, waitFor } from "@testing-library/react";
import { http, HttpResponse, delay } from "msw";
import { describe, expect, it, vi } from "vitest";

import { setSessionExpiredHandler } from "../../../shared/api/client";
import { renderHookWithProviders as renderHook } from "../../../test/render";
import { server } from "../../../test/server";
import { useMovements } from "../../movements/useMovements";
import { useWallet } from "../../wallet/useWallet";
import { PHONE_MESSAGE, RANGE_MESSAGE, FORMAT_MESSAGE, useTransfer } from "../useTransfer";

const PREVIEW = "/api/v1/transfers/preview";

const SUMMARY = {
  amount: "150000.00",
  recipient: { name_masked: null, phone_masked: "***4567" },
  balance_after: "350000.00",
};

function problem(
  status: number,
  code: string,
  detail: string,
  errors?: { field: string; message: string }[],
) {
  return HttpResponse.json(
    { type: "t", title: code, status, code, detail, errors },
    { status, headers: { "Content-Type": "application/problem+json" } },
  );
}

function fill(result: { current: ReturnType<typeof useTransfer> }, phone: string, amount: string) {
  act(() => {
    result.current.setRecipientPhone(phone);
    result.current.setAmount(amount);
  });
}

describe("useTransfer · preparar (HU-06)", () => {
  it("envía teléfono y monto canónicos sin Idempotency-Key y muestra el resumen (CA-1, CA-7, CA-8)", async () => {
    const seen: { headers: Headers; body: unknown }[] = [];
    server.use(
      http.post(PREVIEW, async ({ request }) => {
        seen.push({ headers: request.headers, body: await request.json() });
        return HttpResponse.json(SUMMARY);
      }),
    );
    const { result } = renderHook(() => useTransfer());

    fill(result, "300 123-4567", "150.000");
    await act(() => result.current.review());

    expect(seen[0]?.body).toEqual({ recipient_phone: "3001234567", amount: "150000.00" });
    expect(seen[0]?.headers.get("X-Requested-With")).toBe("fetch");
    expect(seen[0]?.headers.get("Idempotency-Key")).toBeNull();
    expect(result.current.state).toEqual({ kind: "summary", preview: SUMMARY, message: null });
  });

  it("edit() vuelve al formulario conservando los datos", async () => {
    server.use(http.post(PREVIEW, () => HttpResponse.json(SUMMARY)));
    const { result } = renderHook(() => useTransfer());
    fill(result, "3001234567", "150000");
    await act(() => result.current.review());

    act(() => {
      result.current.edit();
    });

    expect(result.current.state).toEqual({ kind: "form", message: null });
    expect(result.current.recipientPhone).toBe("3001234567");
    expect(result.current.amount).toBe("150000");
  });

  it("valida formato y rango en cliente sin llamar a la API (CA-2, CA-3, CA-4)", async () => {
    const spy = vi.fn();
    server.use(http.post(PREVIEW, spy));
    const { result } = renderHook(() => useTransfer());

    fill(result, "12", "99");
    await act(() => result.current.review());
    expect(result.current.fieldErrors).toEqual({
      recipientPhone: PHONE_MESSAGE,
      amount: RANGE_MESSAGE,
    });

    fill(result, "3001234567", "abc");
    await act(() => result.current.review());
    expect(result.current.fieldErrors).toEqual({ amount: FORMAT_MESSAGE });

    fill(result, "3001234567", "3000000.01");
    await act(() => result.current.review());
    expect(result.current.fieldErrors.amount).toBe(RANGE_MESSAGE);

    expect(spy).not.toHaveBeenCalled();
    expect(result.current.state.kind).toBe("form");
  });

  it("mapea el 422 validation del servidor campo a campo (RNF-03.2)", async () => {
    server.use(
      http.post(PREVIEW, () =>
        problem(422, "validation", "Revisa los campos.", [
          { field: "recipient_phone", message: "Teléfono no válido." },
          { field: "amount", message: "Monto no válido." },
        ]),
      ),
    );
    const { result } = renderHook(() => useTransfer());

    fill(result, "3001234567", "1000");
    await act(() => result.current.review());

    expect(result.current.fieldErrors).toEqual({
      recipientPhone: "Teléfono no válido.",
      amount: "Monto no válido.",
    });
  });

  it.each([
    ["recipient_not_found", 404, "El teléfono no corresponde a un usuario registrado."],
    ["self_transfer", 422, "No puedes transferirte a tu propia cuenta."],
    ["insufficient_balance", 422, "Tu saldo es menor que el monto de la transferencia."],
    ["wallet_not_found", 404, "Tu cuenta no tiene una billetera asociada."],
    ["amount_out_of_range", 422, RANGE_MESSAGE],
    ["algo_nuevo", 500, "No se pudo preparar la transferencia. Intenta de nuevo."],
  ])("muestra un mensaje por código para %s (CA-4, CA-5, CA-6)", async (code, status, message) => {
    server.use(http.post(PREVIEW, () => problem(status, code, "detalle del servidor")));
    const { result } = renderHook(() => useTransfer());

    fill(result, "3001234567", "1000");
    await act(() => result.current.review());

    expect(result.current.state).toEqual({ kind: "form", message });
  });

  it("informa falta de conexión cuando la respuesta no es un problem", async () => {
    server.use(http.post(PREVIEW, () => HttpResponse.error()));
    const { result } = renderHook(() => useTransfer());

    fill(result, "3001234567", "1000");
    await act(() => result.current.review());

    expect(result.current.state).toEqual({
      kind: "form",
      message: "No se pudo conectar con el servicio.",
    });
  });

  it("ante 401 invalid_session invoca el manejador de sesión y no muestra resumen (HU-04 CA-2)", async () => {
    const onExpired = vi.fn();
    setSessionExpiredHandler(onExpired);
    server.use(http.post(PREVIEW, () => problem(401, "invalid_session", "Inicia sesión.")));
    const { result } = renderHook(() => useTransfer());

    fill(result, "3001234567", "1000");
    await act(() => result.current.review());

    expect(onExpired).toHaveBeenCalledTimes(1);
    expect(result.current.state.kind).toBe("form");
  });

  it("cambiar un campo limpia sus errores", async () => {
    const { result } = renderHook(() => useTransfer());
    fill(result, "12", "99");
    await act(() => result.current.review());

    act(() => {
      result.current.setAmount("1000");
    });

    expect(result.current.fieldErrors).toEqual({ recipientPhone: PHONE_MESSAGE });
  });
});

const TRANSFERS = "/api/v1/transfers";

const CREATED = {
  id: 8812,
  type: "transferencia",
  status: "exitosa",
  amount: "150000.00",
  recipient: { name_masked: null, phone_masked: "***4567" },
  balance_after: "350000.00",
  created_at: "2026-10-14T21:40:00Z",
};

async function reachSummary(result: { current: ReturnType<typeof useTransfer> }) {
  fill(result, "3001234567", "150000");
  await act(() => result.current.review());
  expect(result.current.state.kind).toBe("summary");
}

describe("useTransfer · confirmar (HU-07)", () => {
  it("solo ejecuta al confirmar y envía la Idempotency-Key del resumen (CA-1, CA-8)", async () => {
    const seen: { headers: Headers; body: unknown }[] = [];
    let calls = 0;
    server.use(
      http.post(PREVIEW, () => HttpResponse.json(SUMMARY)),
      http.post(TRANSFERS, async ({ request }) => {
        calls += 1;
        seen.push({ headers: request.headers, body: await request.json() });
        return HttpResponse.json(CREATED, { status: 201 });
      }),
    );
    const { result } = renderHook(() => useTransfer());

    await reachSummary(result);
    expect(calls).toBe(0);
    await act(() => result.current.confirm());

    expect(result.current.state).toEqual({ kind: "success", result: CREATED });
    expect(seen[0]?.body).toEqual({ recipient_phone: "3001234567", amount: "150000.00" });
    expect(seen[0]?.headers.get("X-Requested-With")).toBe("fetch");
    expect(seen[0]?.headers.get("Idempotency-Key")).toMatch(/^[0-9a-f-]{36}$/);
  });

  it("un doble envío en vuelo produce una sola petición con la misma clave (CA-8)", async () => {
    const keys: string[] = [];
    server.use(
      http.post(PREVIEW, () => HttpResponse.json(SUMMARY)),
      http.post(TRANSFERS, async ({ request }) => {
        keys.push(request.headers.get("Idempotency-Key") ?? "");
        await delay(100);
        return HttpResponse.json(CREATED, { status: 201 });
      }),
    );
    const { result } = renderHook(() => useTransfer());
    await reachSummary(result);

    let first: Promise<void> = Promise.resolve();
    act(() => {
      first = result.current.confirm();
    });
    expect(result.current.state.kind).toBe("confirming");
    await act(() => result.current.confirm());
    await act(() => first);

    expect(keys).toHaveLength(1);
  });

  it("tras un fallo de conexión reintenta con la MISMA clave y no duplica (CA-8)", async () => {
    const keys: string[] = [];
    let attempt = 0;
    server.use(
      http.post(PREVIEW, () => HttpResponse.json(SUMMARY)),
      http.post(TRANSFERS, ({ request }) => {
        keys.push(request.headers.get("Idempotency-Key") ?? "");
        attempt += 1;
        return attempt === 1
          ? HttpResponse.error()
          : HttpResponse.json(CREATED, { status: 201, headers: { "Idempotent-Replayed": "true" } });
      }),
    );
    const { result } = renderHook(() => useTransfer());
    await reachSummary(result);

    await act(() => result.current.confirm());
    expect(result.current.state).toMatchObject({
      kind: "summary",
      message: "No se pudo conectar con el servicio. Puedes reintentar: no se duplicará.",
    });
    await act(() => result.current.confirm());

    expect(keys[0]).toBe(keys[1]);
    expect(result.current.state.kind).toBe("success");
  });

  it("volver a revisar tras editar genera una clave nueva", async () => {
    const keys: string[] = [];
    server.use(
      http.post(PREVIEW, () => HttpResponse.json(SUMMARY)),
      http.post(TRANSFERS, ({ request }) => {
        keys.push(request.headers.get("Idempotency-Key") ?? "");
        return HttpResponse.json(CREATED, { status: 201 });
      }),
    );
    const { result } = renderHook(() => useTransfer());
    await reachSummary(result);
    act(() => {
      result.current.edit();
    });
    await act(() => result.current.review());
    await act(() => result.current.confirm());
    act(() => {
      result.current.reset();
    });
    await reachSummary(result);
    await act(() => result.current.confirm());

    expect(keys[0]).not.toBe(keys[1]);
  });

  it.each([
    ["insufficient_balance", 422, "Tu saldo es menor que el monto de la transferencia."],
    ["recipient_not_found", 404, "El teléfono no corresponde a un usuario registrado."],
    ["algo_nuevo", 400, "No se pudo completar la transferencia. Intenta de nuevo."],
  ])(
    "informa el rechazo de %s sin mostrar éxito (CA-2, CA-6, CA-7)",
    async (code, status, message) => {
      server.use(
        http.post(PREVIEW, () => HttpResponse.json(SUMMARY)),
        http.post(TRANSFERS, () => problem(status, code, "detalle del servidor")),
      );
      const { result } = renderHook(() => useTransfer());
      await reachSummary(result);

      await act(() => result.current.confirm());

      expect(result.current.state).toEqual({ kind: "rejected", message });
    },
  );

  it("en rejected, edit() vuelve al formulario con los datos escritos", async () => {
    server.use(
      http.post(PREVIEW, () => HttpResponse.json(SUMMARY)),
      http.post(TRANSFERS, () => problem(422, "insufficient_balance", "x")),
    );
    const { result } = renderHook(() => useTransfer());
    await reachSummary(result);
    await act(() => result.current.confirm());

    act(() => {
      result.current.edit();
    });

    expect(result.current.state).toEqual({ kind: "form", message: null });
    expect(result.current.amount).toBe("150000");
  });

  it("un 5xx permite reintentar desde el resumen con la misma clave", async () => {
    server.use(
      http.post(PREVIEW, () => HttpResponse.json(SUMMARY)),
      http.post(TRANSFERS, () => problem(503, "internal_error", "x")),
    );
    const { result } = renderHook(() => useTransfer());
    await reachSummary(result);

    await act(() => result.current.confirm());

    expect(result.current.state).toMatchObject({ kind: "summary" });
  });

  it("confirm() sin resumen no hace nada", async () => {
    const { result } = renderHook(() => useTransfer());

    await act(() => result.current.confirm());

    expect(result.current.state).toEqual({ kind: "form", message: null });
  });

  it("ante 401 invalid_session invoca el manejador y no muestra éxito (HU-04 CA-2)", async () => {
    const onExpired = vi.fn();
    setSessionExpiredHandler(onExpired);
    server.use(
      http.post(PREVIEW, () => HttpResponse.json(SUMMARY)),
      http.post(TRANSFERS, () => problem(401, "invalid_session", "Inicia sesión.")),
    );
    const { result } = renderHook(() => useTransfer());
    await reachSummary(result);

    await act(() => result.current.confirm());

    expect(onExpired).toHaveBeenCalledTimes(1);
    expect(result.current.state.kind).not.toBe("success");
  });

  it("invalida saldo y movimientos tras una transferencia exitosa (CA-5, HU-05 CA-3)", async () => {
    let wallet = 0;
    let movements = 0;
    server.use(
      http.post(PREVIEW, () => HttpResponse.json(SUMMARY)),
      http.post(TRANSFERS, () => HttpResponse.json(CREATED, { status: 201 })),
      http.get("/api/v1/wallet", () => {
        wallet += 1;
        return HttpResponse.json({ balance: "500000.00" });
      }),
      http.get("/api/v1/movements", () => {
        movements += 1;
        return HttpResponse.json({ items: [], page: 1, page_size: 20, total: 0 });
      }),
    );
    const { result } = renderHook(() => ({
      transfer: useTransfer(),
      wallet: useWallet(),
      movements: useMovements({ page: 1, from: "", to: "", type: "all" }),
    }));
    await waitFor(() => {
      expect(result.current.wallet.data).toBeDefined();
      expect(result.current.movements.data).toBeDefined();
    });

    act(() => {
      result.current.transfer.setRecipientPhone("3001234567");
      result.current.transfer.setAmount("150000");
    });
    await act(() => result.current.transfer.review());
    expect(wallet).toBe(1);
    expect(movements).toBe(1);

    await act(() => result.current.transfer.confirm());

    await waitFor(() => {
      expect(wallet).toBe(2);
      expect(movements).toBe(2);
    });
  });
});
