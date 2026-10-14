import { IonButton } from "@ionic/react";
import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useSession } from "./useSession";

/**
 * Guardián de las rutas privadas (RNF-01.1, HU-04 CA-2): sin sesión válida no se renderiza
 * nada del área privada y se va a /login. Solo un 401 expulsa; un fallo de red o un 5xx
 * ofrece reintentar y, si ya hubo una sesión verificada, deja seguir usando la pantalla.
 */
export function RequireSession({ children }: { children: ReactNode }) {
  const session = useSession();

  if (session.isUnauthorized) return <Navigate to="/login" replace />;
  if (session.data !== undefined) return <>{children}</>;
  if (session.isError) {
    return (
      <div role="alert" className="tai-card" style={{ margin: 24 }}>
        <p style={{ margin: "0 0 12px" }}>No se pudo verificar la sesión.</p>
        <IonButton
          fill="outline"
          onClick={() => {
            void session.refetch();
          }}
        >
          Reintentar
        </IonButton>
      </div>
    );
  }
  return (
    <p role="status" className="tai-muted" style={{ margin: 24 }}>
      Verificando sesión…
    </p>
  );
}
