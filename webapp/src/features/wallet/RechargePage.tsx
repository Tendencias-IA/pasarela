import {
  IonButton,
  IonButtons,
  IonChip,
  IonContent,
  IonHeader,
  IonInput,
  IonMenuButton,
  IonPage,
  IonTitle,
  IonToolbar,
} from "@ionic/react";
import type { FormEvent } from "react";

import { RECHARGE_MAX, RECHARGE_MIN, formatCOP } from "../../shared/money";
import { ResultBanner } from "../../shared/ui/ResultBanner";
import { useRecharge } from "./useRecharge";

const SUGGESTED = ["20000", "50000", "100000"];

/** HU-08: pantalla "Recargar saldo" según el diseño del equipo. */
export function RechargePage() {
  const { amount, setAmount, fieldError, state, submit, reset } = useRecharge();
  const submitting = state.kind === "submitting";

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    void submit();
  };

  return (
    <IonPage>
      <IonHeader>
        <IonToolbar>
          <IonButtons slot="start">
            <IonMenuButton />
          </IonButtons>
          <IonTitle>Recargar</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent className="ion-padding">
        <h1 className="tai-title">Recargar saldo</h1>
        <p className="tai-muted">
          Entre {formatCOP(RECHARGE_MIN)} y {formatCOP(RECHARGE_MAX)} COP. Dinero ficticio, sin
          medios de pago reales.
        </p>
        <section
          className="tai-card"
          style={{ marginTop: 24 }}
          aria-labelledby="recarga-form-title"
        >
          {state.kind !== "success" && (
            <form
              onSubmit={onSubmit}
              noValidate
              style={{ display: "flex", flexDirection: "column", gap: 18 }}
            >
              <h2 id="recarga-form-title" style={{ margin: 0, fontSize: 17 }}>
                Monto
              </h2>
              <div>
                <p className="tai-muted" style={{ fontWeight: 600, marginBottom: 8 }}>
                  Montos sugeridos
                </p>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {SUGGESTED.map((value) => (
                    <IonChip
                      key={value}
                      role="button"
                      tabIndex={0}
                      outline={amount !== value}
                      color="primary"
                      disabled={submitting}
                      onClick={() => {
                        setAmount(value);
                      }}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") setAmount(value);
                      }}
                    >
                      {formatCOP(`${value}.00`)}
                    </IonChip>
                  ))}
                </div>
              </div>
              <IonInput
                label="Monto a recargar (COP)"
                labelPlacement="stacked"
                inputmode="decimal"
                placeholder="100.000"
                required
                fill="outline"
                value={amount}
                disabled={submitting}
                helperText={`Entre ${formatCOP(RECHARGE_MIN)} y ${formatCOP(RECHARGE_MAX)} COP.`}
                errorText={fieldError ?? undefined}
                className={fieldError ? "ion-invalid ion-touched" : ""}
                onIonInput={(event) => {
                  setAmount(event.detail.value ?? "");
                }}
              />
              {state.kind === "rejected" && fieldError === null && (
                <ResultBanner kind="rejected" title="Recarga rechazada">
                  <p style={{ margin: "4px 0 0", fontSize: 14 }}>{state.message}</p>
                </ResultBanner>
              )}
              <IonButton type="submit" disabled={submitting} style={{ alignSelf: "flex-start" }}>
                {submitting ? "Recargando…" : "Recargar"}
              </IonButton>
            </form>
          )}
          {state.kind === "success" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <ResultBanner
                kind="success"
                title={`Recarga exitosa de ${formatCOP(state.result.amount)}.`}
              >
                <p className="tai-muted" style={{ marginTop: 4 }}>
                  Nuevo saldo disponible:{" "}
                  <strong className="tai-amount" style={{ color: "var(--ion-text-color)" }}>
                    {formatCOP(state.result.balance_after)}
                  </strong>
                </p>
              </ResultBanner>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <IonButton routerLink="/">Volver al panel</IonButton>
                <IonButton fill="outline" onClick={reset}>
                  Hacer otra recarga
                </IonButton>
              </div>
            </div>
          )}
        </section>
      </IonContent>
    </IonPage>
  );
}
