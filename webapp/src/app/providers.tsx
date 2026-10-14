import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { IonReactRouter } from "@ionic/react-router";
import type { PropsWithChildren } from "react";

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
export function AppProviders({ children }: PropsWithChildren) {
  return (
    <QueryClientProvider client={queryClient}>
      <IonReactRouter>{children}</IonReactRouter>
    </QueryClientProvider>
  );
}
