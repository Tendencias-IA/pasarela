import {
  IonButton,
  IonContent,
  IonHeader,
  IonInput,
  IonPage,
  IonTitle,
  IonToolbar,
} from "@ionic/react";
import { type FormEvent, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import "./auth.css";
import { useLogin } from "./useLogin";

const PHONE_PATTERN = /^3\d{9}$/;

/** HU-02: iniciar sesión con teléfono y contraseña. Diseño del equipo (pantalla Iniciar sesión). */
export function LoginPage() {
  const { state, submit } = useLogin();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const expired = params.get("motivo") === "expirada";
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [formatError, setFormatError] = useState<string | null>(null);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!PHONE_PATTERN.test(phone) || password.length < 8) {
      // Feedback inmediato en el cliente; la decisión final siempre es del servidor.
      setFormatError(
        "Ingresa un teléfono de 10 dígitos y una contraseña de al menos 8 caracteres.",
      );
      return;
    }
    setFormatError(null);
    submit({ phone, password });
  };

  // Sesión iniciada: al panel (el historial del navegador no vuelve al formulario).
  useEffect(() => {
    if (state.kind === "success") {
      navigate("/", { replace: true });
    }
  }, [state.kind, navigate]);

  const errorMessage = formatError ?? (state.kind === "error" ? state.message : null);
  const pending = state.kind === "pending";

  return (
    <IonPage>
      <IonHeader>
        <IonToolbar color="dark">
          <IonTitle>TAI</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent>
        <div className="auth-layout">
          <section className="auth-brand">
            <div>
              <h1>TAI</h1>
              <p>
                Tu dinero, bajo control. Transfiere, recarga y revisa tu saldo en un solo lugar.
              </p>
            </div>
            <p style={{ fontSize: "13px", color: "#9fb0a8" }}>
              Prototipo académico — dinero y datos ficticios.
            </p>
          </section>

          <section className="auth-form-panel">
            <form onSubmit={handleSubmit} aria-label="Iniciar sesión">
              <h2 style={{ margin: 0 }}>Bienvenido de nuevo</h2>
              <p style={{ margin: 0, color: "var(--ion-color-medium)" }}>
                Ingresa con tu teléfono y contraseña.
              </p>

              <IonInput
                label="Teléfono"
                labelPlacement="stacked"
                type="tel"
                inputmode="numeric"
                placeholder="3009876543"
                required
                aria-required="true"
                value={phone}
                disabled={pending}
                onIonInput={(e) => {
                  setPhone(e.detail.value ?? "");
                }}
              />

              <IonInput
                label="Contraseña"
                labelPlacement="stacked"
                type="password"
                placeholder="••••••••"
                required
                aria-required="true"
                value={password}
                disabled={pending}
                onIonInput={(e) => {
                  setPassword(e.detail.value ?? "");
                }}
              />

              {expired && state.kind === "idle" && (
                <p role="status" className="auth-notice">
                  Tu sesión expiró. Inicia sesión de nuevo.
                </p>
              )}
              {errorMessage && (
                <p role="alert" className="auth-error">
                  {errorMessage}
                </p>
              )}
              {state.kind === "success" && (
                <p role="status" className="auth-success">
                  Acceso verificado.
                </p>
              )}

              <IonButton type="submit" expand="block" disabled={pending}>
                {pending ? "Ingresando…" : "Iniciar sesión"}
              </IonButton>
            </form>
          </section>
        </div>
      </IonContent>
    </IonPage>
  );
}
