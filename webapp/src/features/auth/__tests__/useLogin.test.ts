import { act, renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "../../../test/server";
import { useLogin } from "../useLogin";

/**
 * Cubre la lógica de useLogin sin pasar por el shadow DOM de IonInput, que
 * @testing-library/dom no puede consultar con getByLabelText en jsdom (los
 * tests que sí montaban <LoginPage/> con inputs reales se retiraron por eso,
 * ver PR). El comportamiento del formulario (validación de formato) se cubre
 * en e2e/hu-02-iniciar-sesion.spec.ts contra un navegador real.
 */
describe("useLogin", () => {
  it("HU-02 CA-1: credenciales correctas terminan en éxito", async () => {
    server.use(http.post("/api/v1/auth/login", () => new HttpResponse(null, { status: 204 })));
    const { result } = renderHook(() => useLogin());

    act(() => {
      result.current.submit({ phone: "3009876543", password: "Clave1234" });
    });

    await waitFor(() => {
      expect(result.current.state.kind).toBe("success");
    });
  });

  it("HU-02 CA-2, CA-3: teléfono inexistente y contraseña incorrecta dan el mismo mensaje", async () => {
    const problem = {
      type: "x",
      title: "Teléfono o contraseña incorrectos",
      status: 401,
      instance: "/api/v1/auth/login",
      code: "invalid_credentials",
    };
    server.use(
      http.post("/api/v1/auth/login", () =>
        HttpResponse.json(problem, {
          status: 401,
          headers: { "Content-Type": "application/problem+json" },
        }),
      ),
    );

    const unknownPhone = renderHook(() => useLogin());
    act(() => {
      unknownPhone.result.current.submit({ phone: "3000000000", password: "cualquiera123" });
    });
    await waitFor(() => {
      expect(unknownPhone.result.current.state.kind).toBe("error");
    });

    const wrongPassword = renderHook(() => useLogin());
    act(() => {
      wrongPassword.result.current.submit({ phone: "3009876543", password: "incorrecta123" });
    });
    await waitFor(() => {
      expect(wrongPassword.result.current.state.kind).toBe("error");
    });

    const unknownState = unknownPhone.result.current.state;
    const wrongState = wrongPassword.result.current.state;
    if (unknownState.kind !== "error" || wrongState.kind !== "error") {
      throw new Error("se esperaba estado de error en ambos casos");
    }
    expect(unknownState.message).toBe(wrongState.message);
  });
});
