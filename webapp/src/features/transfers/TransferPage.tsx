import {
  IonButton,
  IonButtons,
  IonContent,
  IonHeader,
  IonInput,
  IonMenuButton,
  IonPage,
  IonTitle,
  IonToolbar,
} from "@ionic/react";
import type { FormEvent } from "react";

import { TRANSFER_MAX, TRANSFER_MIN, formatCOP } from "../../shared/money";
import { ResultBanner } from "../../shared/ui/ResultBanner";
import { useTransfer } from "./useTransfer";

/** HU-06: formulario (teléfono + monto) y resumen para revisar antes de confirmar. */
export function TransferPage() {
  const {
    recipientPhone,
    setRecipientPhone,
    amount,
    setAmount,
    fieldErrors,
    state,
    review,
    edit,
    confirm,
    reset,
  } = useTransfer();
  const busy = state.kind === "previewing";

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    void review();
  };

  return (
    <IonPage>
      <IonHeader>
        <IonToolbar>
          <IonButtons slot="start">
            <IonMenuButton />
          </IonButtons>
          <IonTitle>Transferir</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent className="ion-padding">
        <h1 className="tai-title">Transferir dinero</h1>
        <p className="tai-muted">
          Entre {formatCOP(TRANSFER_MIN)} y {formatCOP(TRANSFER_MAX)} COP. Dinero ficticio entre
          usuarios del prototipo.
        </p>
        <section className="tai-card" style={{ marginTop: 24 }} aria-labelledby="transfer-title">
          {(state.kind === "form" || state.kind === "previewing") && (
            <form
              onSubmit={onSubmit}
              noValidate
              style={{ display: "flex", flexDirection: "column", gap: 18 }}
            >
              <h2 id="transfer-title" style={{ margin: 0, fontSize: 17 }}>
                Datos de la transferencia
              </h2>
              <IonInput
                label="Teléfono del destinatario"
                labelPlacement="stacked"
                inputmode="tel"
                placeholder="3001234567"
                required
                fill="outline"
                value={recipientPhone}
                disabled={busy}
                errorText={fieldErrors.recipientPhone}
                className={fieldErrors.recipientPhone ? "ion-invalid ion-touched" : ""}
                onIonInput={(event) => {
                  setRecipientPhone(event.detail.value ?? "");
                }}
              />
              <IonInput
                label="Monto (COP)"
                labelPlacement="stacked"
                inputmode="decimal"
                placeholder="150.000"
                required
                fill="outline"
                value={amount}
                disabled={busy}
                errorText={fieldErrors.amount}
                className={fieldErrors.amount ? "ion-invalid ion-touched" : ""}
                onIonInput={(event) => {
                  setAmount(event.detail.value ?? "");
                }}
              />
              {state.kind === "form" && state.message !== null && (
                <ResultBanner kind="rejected" title="No se pudo preparar la transferencia">
                  <p style={{ margin: "4px 0 0", fontSize: 14 }}>{state.message}</p>
                </ResultBanner>
              )}
              <IonButton type="submit" disabled={busy} style={{ alignSelf: "flex-start" }}>
                {busy ? "Revisando…" : "Revisar"}
              </IonButton>
            </form>
          )}
          {(state.kind === "summary" || state.kind === "confirming") && (
            <section aria-labelledby="resumen-title">
              <h2 id="resumen-title" style={{ margin: "0 0 12px", fontSize: 17 }}>
                Resumen de la transferencia
              </h2>
              <dl style={{ margin: 0, display: "grid", gap: 8 }}>
                <div>
                  <dt className="tai-muted">Destinatario</dt>
                  <dd style={{ margin: 0 }}>
                    {state.preview.recipient.name_masked !== null && (
                      <strong>{state.preview.recipient.name_masked} </strong>
                    )}
                    <span>{state.preview.recipient.phone_masked}</span>
                  </dd>
                </div>
                <div>
                  <dt className="tai-muted">Monto</dt>
                  <dd className="tai-amount" style={{ margin: 0 }}>
                    {formatCOP(state.preview.amount)}
                  </dd>
                </div>
                <div>
                  <dt className="tai-muted">Saldo después</dt>
                  <dd className="tai-amount" style={{ margin: 0 }}>
                    {formatCOP(state.preview.balance_after)}
                  </dd>
                </div>
              </dl>
              {state.kind === "summary" && state.message !== null && (
                <div style={{ marginTop: 12 }}>
                  <ResultBanner kind="rejected" title="No se pudo confirmar todavía">
                    <p style={{ margin: "4px 0 0", fontSize: 14 }}>{state.message}</p>
                  </ResultBanner>
                </div>
              )}
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 16 }}>
                <IonButton
                  disabled={state.kind === "confirming"}
                  onClick={() => {
                    void confirm();
                  }}
                >
                  {state.kind === "confirming" ? "Confirmando…" : "Confirmar"}
                </IonButton>
                <IonButton fill="outline" disabled={state.kind === "confirming"} onClick={edit}>
                  Editar
                </IonButton>
              </div>
            </section>
          )}
          {state.kind === "success" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <ResultBanner
                kind="success"
                title={`Transferencia exitosa de ${formatCOP(state.result.amount)}.`}
              >
                <p className="tai-muted" style={{ marginTop: 4 }}>
                  Enviada a {state.result.recipient.name_masked ?? "destinatario"}{" "}
                  {state.result.recipient.phone_masked}. Nuevo saldo disponible:{" "}
                  <strong className="tai-amount" style={{ color: "var(--ion-text-color)" }}>
                    {formatCOP(state.result.balance_after)}
                  </strong>
                </p>
              </ResultBanner>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <IonButton routerLink="/">Volver al panel</IonButton>
                <IonButton fill="outline" onClick={reset}>
                  Hacer otra transferencia
                </IonButton>
              </div>
            </div>
          )}
          {state.kind === "rejected" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <ResultBanner kind="rejected" title="Transferencia rechazada">
                <p style={{ margin: "4px 0 0", fontSize: 14 }}>{state.message}</p>
                <p className="tai-muted" style={{ margin: "4px 0 0" }}>
                  No se movió dinero de tu cuenta.
                </p>
              </ResultBanner>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <IonButton onClick={edit}>Editar datos</IonButton>
                <IonButton fill="outline" routerLink="/">
                  Volver al panel
                </IonButton>
              </div>
            </div>
          )}
        </section>
      </IonContent>
    </IonPage>
  );
}
