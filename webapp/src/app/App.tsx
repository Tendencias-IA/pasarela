import {
  IonApp,
  IonContent,
  IonHeader,
  IonPage,
  IonRouterOutlet,
  IonTitle,
  IonToolbar,
} from "@ionic/react";
import { IonReactRouter } from "@ionic/react-router";
import { useEffect, useState } from "react";
import { Route } from "react-router-dom";

import { LoginPage } from "../features/auth/LoginPage";
import { ApiError } from "../shared/api/client";
import { getHealth, type Health } from "./health";

type State =
  { kind: "loading" } | { kind: "ready"; health: Health } | { kind: "error"; message: string };

export function App() {
  return (
    <IonApp>
      <IonReactRouter>
        <IonRouterOutlet>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<HealthStatusPage />} />
        </IonRouterOutlet>
      </IonReactRouter>
    </IonApp>
  );
}

/** Pantalla provisional de arranque: muestra el estado de la API hasta que exista un panel. */
function HealthStatusPage() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    getHealth(controller.signal)
      .then((health) => {
        setState({ kind: "ready", health });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const message =
          error instanceof ApiError ? `${error.code} (${String(error.status)})` : "sin conexión";
        setState({ kind: "error", message });
      });
    return () => {
      controller.abort();
    };
  }, []);

  return (
    <IonPage>
      <IonHeader>
        <IonToolbar color="primary">
          <IonTitle>Billetera Digital</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent className="ion-padding">
        <main>
          <h1>Billetera Digital</h1>
          <section aria-labelledby="estado-api">
            <h2 id="estado-api">Estado de la API</h2>
            {state.kind === "loading" && <p role="status">Consultando…</p>}
            {state.kind === "ready" && (
              <p role="status" data-health={state.health.status}>
                API {state.health.status}, base de datos {state.health.db}
              </p>
            )}
            {state.kind === "error" && (
              <p role="alert">No se pudo consultar la API: {state.message}</p>
            )}
          </section>
        </main>
      </IonContent>
    </IonPage>
  );
}
