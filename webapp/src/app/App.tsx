import { IonApp } from "@ionic/react";
import { QueryClientProvider } from "@tanstack/react-query";

import { queryClient } from "./queryClient";
import { AppRoutes } from "./routes";

export function App() {
  return (
    <IonApp>
      <QueryClientProvider client={queryClient}>
        <AppRoutes />
      </QueryClientProvider>
    </IonApp>
  );
}
