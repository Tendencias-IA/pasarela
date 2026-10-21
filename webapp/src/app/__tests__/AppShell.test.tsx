import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { renderWithProviders as render } from "../../test/render";
import { AppShell } from "../AppShell";

const auth = vi.hoisted(() => ({ logout: vi.fn(), failed: false }));
vi.mock("../../features/auth/useLogout", () => ({ useLogout: () => auth }));

describe("AppShell (menú lateral)", () => {
  it("cierra la sesión desde el menú (HU-03 CA-1)", () => {
    auth.failed = false;
    render(<AppShell>contenido</AppShell>);

    const items = document.querySelectorAll("ion-item");
    expect(items).toHaveLength(6);
    expect(screen.queryByRole("alert")).toBeNull();
    const logoutItem = items[items.length - 1] as Element;
    expect(logoutItem).toHaveTextContent("Cerrar sesión");
    fireEvent.click(logoutItem);
    expect(auth.logout).toHaveBeenCalledTimes(1);
  });

  it("avisa cuando no se pudo cerrar la sesión", () => {
    auth.failed = true;
    render(<AppShell>contenido</AppShell>);

    expect(screen.getByRole("alert")).toHaveTextContent("No se pudo cerrar la sesión");
  });
});
