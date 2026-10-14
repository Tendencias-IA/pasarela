import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import type { PropsWithChildren } from "react";
import { describe, expect, it } from "vitest";

import { server } from "../../../test/server";
import { useProfile } from "../useProfile";

const profile = {
  full_name: "Persona Prueba",
  phone: "3001110001",
  national_id: "PRUEBA001",
  email: "persona@example.test",
};
function wrapper({ children }: PropsWithChildren) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>;
}
describe("HU-12 perfil", () => {
  it("CA-3 y CA-4 actualiza la caché después de guardar", async () => {
    server.use(
      http.get("/api/v1/profile", () => HttpResponse.json(profile)),
      http.patch("/api/v1/profile", () => HttpResponse.json({ ...profile, phone: "3001110002" })),
    );
    const { result } = renderHook(() => useProfile(), { wrapper });
    await waitFor(() => {
      expect(result.current.profile.isSuccess).toBe(true);
    });
    await act(async () => {
      await result.current.changePhone.mutateAsync("3001110002");
    });
    await waitFor(() => {
      expect(result.current.profile.data?.phone).toBe("3001110002");
    });
  });
  it("CA-2 y CA-8 conserva el perfil cuando el servidor rechaza", async () => {
    server.use(
      http.get("/api/v1/profile", () => HttpResponse.json(profile)),
      http.patch("/api/v1/profile", () =>
        HttpResponse.json(
          {
            type: "https://pasarela.local/problems/duplicate_identity",
            title: "Duplicado",
            status: 409,
            code: "duplicate_identity",
          },
          { status: 409 },
        ),
      ),
    );
    const { result } = renderHook(() => useProfile(), { wrapper });
    await waitFor(() => {
      expect(result.current.profile.isSuccess).toBe(true);
    });
    await act(async () => {
      await expect(result.current.changePhone.mutateAsync("3001110002")).rejects.toThrow();
    });
    expect(result.current.profile.data?.phone).toBe(profile.phone);
  });
});
