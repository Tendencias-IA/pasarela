import { IonApp, IonContent, IonHeader, IonPage, IonTitle, IonToolbar } from "@ionic/react";
import { useEffect, useState } from "react";

import { ApiError } from "../shared/api/client";
import { getHealth, type Health } from "./health";

type State =
  { kind: "loading" } | { kind: "ready"; health: Health } | { kind: "error"; message: string };

/** Pantalla inicial del esqueleto: muestra el estado de la API. Las features llegan con las HU. */
export function App() {
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
    <IonApp>
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
    </IonApp>
  );
}
