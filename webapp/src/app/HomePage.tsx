import {
  IonButton,
  IonButtons,
  IonContent,
  IonHeader,
  IonMenuButton,
  IonPage,
  IonTitle,
  IonToolbar,
} from "@ionic/react";
import { useEffect, useState } from "react";

import { useWallet } from "../features/wallet/useWallet";
import { ApiError } from "../shared/api/client";
import { formatCOP } from "../shared/money";
import { getHealth, type Health } from "./health";

type State =
  { kind: "loading" } | { kind: "ready"; health: Health } | { kind: "error"; message: string };

/** Panel inicial del esqueleto. El saldo llega con HU-05; hoy muestra el estado de la API. */
export function HomePage() {
  const [state, setState] = useState<State>({ kind: "loading" });
  const wallet = useWallet();

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
        <IonToolbar>
          <IonButtons slot="start">
            <IonMenuButton />
          </IonButtons>
          <IonTitle>Inicio</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent className="ion-padding">
        <h1 className="tai-title">Billetera Digital</h1>
        <section aria-labelledby="saldo-title" className="tai-card" style={{ marginTop: 16 }}>
          <h2 id="saldo-title" style={{ margin: "0 0 8px", fontSize: 17 }}>
            Saldo disponible
          </h2>
          {wallet.isPending && <p role="status">Consultando saldo…</p>}
          {wallet.data !== undefined && (
            <p className="tai-amount" style={{ margin: 0, fontSize: 28, fontWeight: 700 }}>
              {formatCOP(wallet.data.balance)}
            </p>
          )}
          {wallet.isUnavailable && <p role="alert">Saldo no disponible</p>}
          {wallet.isError && !wallet.isUnavailable && (
            <p role="alert">No se pudo consultar el saldo. Intenta de nuevo.</p>
          )}
        </section>
        <section aria-labelledby="estado-api" className="tai-card" style={{ marginTop: 16 }}>
          <h2 id="estado-api" style={{ margin: "0 0 8px", fontSize: 17 }}>
            Estado de la API
          </h2>
          {state.kind === "loading" && <p role="status">Consultando…</p>}
          {state.kind === "ready" && (
            <p role="status" data-health={state.health.status}>
              API {state.health.status}, base de datos {state.health.db}
            </p>
          )}
          {state.kind === "error" && (
            <p role="alert">No se pudo consultar la API: {state.message}</p>
          )}
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 12 }}>
            <IonButton routerLink="/recargar">Recargar saldo</IonButton>
            <IonButton routerLink="/movimientos" fill="outline">
              Ver movimientos
            </IonButton>
          </div>
        </section>
      </IonContent>
    </IonPage>
  );
}
