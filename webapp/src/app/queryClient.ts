import { QueryClient } from "@tanstack/react-query";

/** Estado del servidor (webapp.md). Sin reintentos: un 4xx no cambia reintentando. */
export function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: 0, refetchOnWindowFocus: false } },
  });
}

export const queryClient = createQueryClient();
