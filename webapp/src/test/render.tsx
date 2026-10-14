import { QueryClientProvider } from "@tanstack/react-query";
import {
  render,
  renderHook,
  type RenderHookOptions,
  type RenderOptions,
} from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";

import { createQueryClient } from "../app/queryClient";

/** Envoltorio de pruebas: QueryClient nuevo por test y router en memoria. */
export function makeWrapper(initialEntries: string[] = ["/"]) {
  const client = createQueryClient();
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={initialEntries}>{children}</MemoryRouter>
      </QueryClientProvider>
    );
  };
}

export function renderWithProviders(
  ui: ReactElement,
  options?: RenderOptions & { route?: string },
) {
  const { route, ...rest } = options ?? {};
  return render(ui, { wrapper: makeWrapper(route ? [route] : undefined), ...rest });
}

export function renderHookWithProviders<Result, Props>(
  hook: (props: Props) => Result,
  options?: RenderHookOptions<Props>,
) {
  return renderHook(hook, { wrapper: makeWrapper(), ...options });
}
