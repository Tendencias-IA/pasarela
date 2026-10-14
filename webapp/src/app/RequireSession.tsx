import { IonButton, IonContent, IonPage } from "@ionic/react";
import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useLocation } from "react-router-dom";

import { getSession } from "../features/auth/api";

/** HU-03 CA-2/CA-3: no montar vistas privadas antes de validar la cookie. */
export function RequireSession({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  const session = useQuery({
    queryKey: ["session", pathname],
    queryFn: ({ signal }) => getSession(signal),
    retry: false,
    staleTime: 0,
    gcTime: 0,
    refetchOnMount: "always",
  });
  if (session.isSuccess && !session.isFetching) return <>{children}</>;
  return (
    <IonPage>
      <IonContent className="ion-padding">
        {session.isPending || session.isFetching ? (
          <p role="status">Verificando sesión…</p>
        ) : (
          <>
            <p role="alert">No se pudo verificar la sesión.</p>
            <IonButton
              onClick={() => {
                void session.refetch();
              }}
            >
              Reintentar
            </IonButton>
          </>
        )}
      </IonContent>
    </IonPage>
  );
}
